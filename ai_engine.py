"""
ai_engine.py
------------
Contains:
  1. generate_load_data()    — Simulates feeder-level hourly load data
  2. nbeats_forecast()       — N-BEATS inspired time-series forecasting
  3. detect_anomalies()      — Adaptive quantile-based anomaly detection + XAI labels
  4. compute_metrics()       — MAE, MAPE, RMSE, Accuracy
"""

import numpy as np
from datetime import datetime, timedelta


# ──────────────────────────────────────────────────────────────
# 1. LOAD DATA GENERATOR
# ──────────────────────────────────────────────────────────────
def generate_load_data(location: str, loc_info: dict, hours: int = 72) -> list:
    """
    Simulate realistic feeder-level hourly electricity load data.

    Pattern:
      - Dual-peak daily cycle  (morning 9-11 AM, evening 7-9 PM)
      - Weekend load reduction (~16% lower)
      - Small Gaussian noise   (±1.5% of load)

    Parameters
    ----------
    location : str       — city name (used as random seed for consistency)
    loc_info : dict      — must have keys 'base' and 'peak' (in MW)
    hours    : int       — number of hourly readings to generate

    Returns
    -------
    list of dicts: [{"timestamp": "...", "actual_load": float}, ...]
    """
    base = loc_info["base"]
    peak = loc_info["peak"]
    np.random.seed(abs(hash(location)) % 9999)   # same city → same data every run

    data = []
    now  = datetime.now()

    for i in range(hours):
        t    = now - timedelta(hours=hours - i)
        hour = t.hour

        # --- Daily seasonality factor ---
        if   9  <= hour <= 11:  seasonal = 0.85   # morning peak
        elif 19 <= hour <= 21:  seasonal = 1.00   # evening peak (highest)
        elif  0 <= hour <=  5:  seasonal = 0.42   # night trough
        elif 12 <= hour <= 14:  seasonal = 0.74   # afternoon
        else:                   seasonal = 0.64   # normal daytime

        # --- Weekend factor ---
        week_factor = 0.84 if t.weekday() >= 5 else 1.0

        # --- Base load + seasonality + noise ---
        load  = base + (peak - base) * seasonal * week_factor
        noise = np.random.normal(0, load * 0.015)
        load  = round(max(base * 0.30, load + noise), 2)

        data.append({
            "timestamp":   t.strftime("%Y-%m-%d %H:%M"),
            "actual_load": load
        })

    return data


# ──────────────────────────────────────────────────────────────
# 2. N-BEATS INSPIRED FORECASTING
# ──────────────────────────────────────────────────────────────
def nbeats_forecast(history: list, steps: int = 48) -> list:
    """
    N-BEATS inspired forecasting using:
      - Trend Block     : Degree-2 polynomial regression
      - Seasonality Block: 24-hour periodic pattern by averaging

    Algorithm steps
    ---------------
    1. Fit polynomial to detect long-term trend.
    2. Remove trend → detrended residuals.
    3. Average detrended values by hour-of-day → 24-h seasonal pattern.
    4. Forecast = trend extrapolation + seasonal component + tiny noise.

    Parameters
    ----------
    history : list of floats — historical load values (MW)
    steps   : int            — number of future hours to forecast

    Returns
    -------
    list of floats (forecasted MW values)
    """
    x = np.array(history, dtype=float)
    n = len(x)
    t = np.arange(n)

    # --- Trend block: degree-2 polynomial ---
    coeffs    = np.polyfit(t, x, 2)
    trend     = np.polyval(coeffs, t)
    detrended = x - trend

    # --- Seasonality block: 24-hour cycle ---
    period  = 24
    pattern = np.zeros(period)
    counts  = np.zeros(period)
    for i, val in enumerate(detrended):
        pattern[i % period] += val
        counts[i % period]  += 1
    counts[counts == 0] = 1
    pattern = pattern / counts          # average seasonal deviation per hour

    # --- Forecast ---
    forecast = []
    for s in range(steps):
        future_t    = n + s
        trend_val   = np.polyval(coeffs, future_t)
        seasonal_val = pattern[future_t % period]
        noise        = np.random.normal(0, abs(trend_val) * 0.012)
        forecast.append(round(max(0.0, trend_val + seasonal_val + noise), 2))

    return forecast


# ──────────────────────────────────────────────────────────────
# 3. ADAPTIVE ANOMALY DETECTION + XAI CLASSIFICATION
# ──────────────────────────────────────────────────────────────
def detect_anomalies(actual: list, forecast: list, timestamps: list) -> list:
    """
    Detects anomalies using Adaptive Quantile-Based Residual Analysis
    and classifies them using Explainable AI (rule-based XAI).

    Steps
    -----
    1. Compute residual: Residual = Actual − Forecast
    2. Use a rolling 12-hour window to compute adaptive threshold
       (95th percentile of |residuals| in the window, minimum 13% of load).
    3. If |Residual| > threshold → anomaly detected.
    4. XAI classification rules:
         • Communication Loss : actual ≈ 0 (< 8% of forecast)
         • Load Spike         : large positive residual (> 1.5× threshold)
         • Meter Fault        : very large negative residual (> 1.8× threshold)
         • Load Drop          : moderate negative residual
         • Demand Drift       : small sustained deviation

    Parameters
    ----------
    actual     : list of floats   — actual load readings (MW)
    forecast   : list of floats   — N-BEATS forecasted values (MW)
    timestamps : list of strings  — timestamp for each reading

    Returns
    -------
    list of anomaly dicts with keys:
        index, timestamp, actual, forecast, residual,
        threshold, pct_deviation, type, severity, explanation
    """
    residuals = [a - f for a, f in zip(actual, forecast)]
    anomalies = []
    window    = 12  # rolling window size (hours)

    for i in range(len(residuals)):
        start      = max(0, i - window)
        window_abs = [abs(r) for r in residuals[start : i + 1]]

        if len(window_abs) < 3:
            continue  # need at least 3 points to form a baseline

        # Adaptive threshold = 95th percentile (min 13% of current load)
        threshold = max(
            float(np.percentile(window_abs, 95)),
            actual[i] * 0.13
        )

        res     = residuals[i]
        abs_res = abs(res)

        if abs_res <= threshold:
            continue  # within normal range

        pct_dev = round(abs_res / max(forecast[i], 1) * 100, 1)

        # ── XAI Classification Rules ──────────────────────────
        if actual[i] < forecast[i] * 0.08:
            atype = "Communication Loss"
            sev   = "Critical"
            expl  = (
                f"Meter reading dropped to near-zero ({actual[i]:.1f} MW) "
                f"against forecast of {forecast[i]:.1f} MW. "
                f"Likely cause: Smart meter communication failure or complete feeder outage."
            )

        elif res > threshold * 1.5:
            atype = "Load Spike"
            sev   = "High" if pct_dev > 35 else "Medium"
            expl  = (
                f"Sudden load surge of +{res:.1f} MW ({pct_dev}% above forecast). "
                f"Likely cause: Unexpected industrial load addition, "
                f"transformer overload, or large unplanned consumer activity."
            )

        elif res < -threshold * 1.8:
            atype = "Meter Fault"
            sev   = "High"
            expl  = (
                f"Rapid load drop of {res:.1f} MW ({pct_dev}% below forecast). "
                f"Likely cause: Meter bypass or tampering (possible power theft), "
                f"or meter hardware fault."
            )

        elif res < -threshold:
            atype = "Load Drop"
            sev   = "Medium"
            expl  = (
                f"Unexplained load reduction of {abs(res):.1f} MW. "
                f"Likely cause: Large consumer tripping, load shedding, "
                f"or renewable generation offset."
            )

        else:
            atype = "Demand Drift"
            sev   = "Low"
            expl  = (
                f"Gradual demand shift of {res:.1f} MW over time. "
                f"Likely cause: Changing consumer behaviour, "
                f"seasonal variation, or EV charging pattern change."
            )

        anomalies.append({
            "index":         i,
            "timestamp":     timestamps[i],
            "actual":        actual[i],
            "forecast":      forecast[i],
            "residual":      round(res, 2),
            "threshold":     round(threshold, 2),
            "pct_deviation": pct_dev,
            "type":          atype,
            "severity":      sev,
            "explanation":   expl,
        })

    return anomalies


# ──────────────────────────────────────────────────────────────
# 4. FORECASTING ACCURACY METRICS
# ──────────────────────────────────────────────────────────────
def compute_metrics(actual: list, forecast: list) -> dict:
    """
    Compute standard forecasting accuracy metrics.

    Metrics
    -------
    MAE      — Mean Absolute Error (MW)
    MAPE     — Mean Absolute Percentage Error (%)
    RMSE     — Root Mean Squared Error (MW)
    Accuracy — 100 - MAPE  (overall % accuracy)
    """
    a = np.array(actual,   dtype=float)
    f = np.array(forecast, dtype=float)

    mae      = float(np.mean(np.abs(a - f)))
    mape     = float(np.mean(np.abs((a - f) / np.maximum(a, 1)))) * 100
    rmse     = float(np.sqrt(np.mean((a - f) ** 2)))
    accuracy = max(0.0, 100.0 - mape)

    return {
        "mae":      round(mae,      2),
        "mape":     round(mape,     2),
        "rmse":     round(rmse,     2),
        "accuracy": round(accuracy, 1),
    }
