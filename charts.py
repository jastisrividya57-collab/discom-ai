"""
charts.py
---------
All Plotly chart functions for the dashboard.
Each function receives the analytics data dict and returns a Plotly Figure.
"""

import plotly.graph_objects as go
from datetime import datetime, timedelta


# ── SHARED DARK-THEME LAYOUT ──────────────────────────────────
BASE_LAYOUT = dict(
    paper_bgcolor = "#0a1525",
    plot_bgcolor  = "#0a1525",
    font          = dict(color="#c0d8e8", family="Exo 2, sans-serif", size=11),
    xaxis         = dict(
        gridcolor="#0d2640",
        tickfont=dict(size=10, color="#4a6a7a"),
        showgrid=True,
    ),
    yaxis         = dict(
        gridcolor="#0d2640",
        tickfont=dict(size=10, color="#4a6a7a"),
        showgrid=True,
    ),
    margin        = dict(l=55, r=20, t=30, b=50),
    hovermode    = "x unified",
    hoverlabel   = dict(
        bgcolor="#0a1525",
        bordercolor="#0d2640",
        font=dict(color="#c0d8e8", size=12),
    ),
)


# ── 1. ACTUAL vs FORECAST (main 48-hour chart) ────────────────
def chart_actual_vs_forecast(data: dict) -> go.Figure:
    """
    Line chart: Actual load (blue) vs N-BEATS forecast (orange dashed).
    Anomaly points are shown as red circles.
    """
    anomaly_indices = {a["index"] for a in data["anomalies"]}
    labels          = [t[11:16] for t in data["timestamps"]]   # show HH:MM only

    # Anomaly y-values: actual load at anomaly index, else None
    anomaly_y = [
        data["actual"][i] if i in anomaly_indices else None
        for i in range(len(data["actual"]))
    ]

    fig = go.Figure()

    # Actual load — filled area
    fig.add_trace(go.Scatter(
        x=labels, y=data["actual"],
        name="Actual Load",
        line=dict(color="#00d4ff", width=2),
        fill="tozeroy",
        fillcolor="rgba(0,212,255,0.06)",
        hovertemplate="Actual: %{y:.1f} MW<extra></extra>",
    ))

    # N-BEATS forecast — dashed line
    fig.add_trace(go.Scatter(
        x=labels, y=data["forecast"],
        name="N-BEATS Forecast",
        line=dict(color="#ff6b2b", width=2, dash="dot"),
        hovertemplate="Forecast: %{y:.1f} MW<extra></extra>",
    ))

    # Anomaly markers
    fig.add_trace(go.Scatter(
        x=labels, y=anomaly_y,
        name="Anomaly",
        mode="markers",
        marker=dict(
            color="#ff4466", size=10, symbol="circle",
            line=dict(color="white", width=1.5),
        ),
        hovertemplate="⚠ Anomaly: %{y:.1f} MW<extra></extra>",
    ))

    fig.update_layout(
        **BASE_LAYOUT,
        height=280,
        yaxis_title="Load (MW)",
        legend=dict(orientation="h", y=-0.25, x=0),
    )
    return fig


# ── 2. RESIDUAL ANALYSIS CHART ───────────────────────────────
def chart_residual(data: dict) -> go.Figure:
    """
    Bar chart of residuals (Actual − Forecast).
    Green bars = positive residual, orange bars = negative.
    Red/orange dashed lines show the adaptive threshold boundaries.
    """
    residuals = [round(a - f, 2) for a, f in zip(data["actual"], data["forecast"])]
    max_res   = max(abs(r) for r in residuals) if residuals else 1
    threshold = max_res * 0.72
    labels    = [t[11:16] for t in data["timestamps"]]

    bar_colors = [
        "rgba(0,255,136,0.55)" if r >= 0 else "rgba(255,107,43,0.55)"
        for r in residuals
    ]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=labels, y=residuals,
        name="Residual (MW)",
        marker_color=bar_colors,
        marker_line_width=0,
        hovertemplate="Residual: %{y:.2f} MW<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=labels, y=[ threshold] * len(labels),
        name="+Threshold",
        line=dict(color="#ff3b5c", width=1.5, dash="dash"),
        mode="lines",
        hoverinfo="skip",
    ))

    fig.add_trace(go.Scatter(
        x=labels, y=[-threshold] * len(labels),
        name="−Threshold",
        line=dict(color="#ff8800", width=1.5, dash="dash"),
        mode="lines",
        hoverinfo="skip",
    ))

    fig.update_layout(
        **BASE_LAYOUT,
        height=230,
        yaxis_title="Residual (MW)",
        legend=dict(orientation="h", y=-0.30, x=0),
        bargap=0.15,
    )
    return fig


# ── 3. 12-HOUR AHEAD FORECAST BAR CHART ──────────────────────
def chart_forecast_12h(data: dict) -> go.Figure:
    """
    Bar chart of the next 12-hour forecasted load.
    Colour changes from blue → orange → red as load approaches peak.
    """
    peak   = data["peak"]
    values = data["next_val"]
    times  = data["next_ts"]

    colors = [
        "#ff3b5c" if v > peak * 0.85 else
        "#ffaa00" if v > peak * 0.70 else
        "#00d4ff"
        for v in values
    ]

    fig = go.Figure(go.Bar(
        x=times, y=values,
        marker_color=colors,
        marker_line_width=0,
        text=[f"{v:.0f}" for v in values],
        textposition="outside",
        textfont=dict(size=10, color="#c0d8e8"),
        hovertemplate="%{x}  →  %{y:.1f} MW<extra></extra>",
    ))

    fig.update_layout(
        **BASE_LAYOUT,
        height=240,
        yaxis_title="Load (MW)",
        showlegend=False,
        bargap=0.3,
    )
    return fig


# ── 4. ANOMALY TYPE DONUT CHART ───────────────────────────────
def chart_anomaly_donut(data: dict) -> go.Figure:
    """
    Donut chart showing the count of each anomaly type.
    Shows a 'No Anomalies' message if the list is empty.
    """
    counts = {}
    for a in data["anomalies"]:
        counts[a["type"]] = counts.get(a["type"], 0) + 1

    fig = go.Figure()

    if not counts:
        fig.add_annotation(
            text="✔ No Anomalies",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="#00ff88"),
        )
        fig.update_layout(**BASE_LAYOUT, height=220, showlegend=False)
        return fig

    color_map = {
        "Load Spike":         "#ff4466",
        "Load Drop":          "#ff8800",
        "Demand Drift":       "#aa66ff",
        "Meter Fault":        "#ff3b5c",
        "Communication Loss": "#ff6600",
    }
    labels = list(counts.keys())

    fig.add_trace(go.Pie(
        labels=labels,
        values=list(counts.values()),
        hole=0.62,
        marker_colors=[color_map.get(l, "#00d4ff") for l in labels],
        textinfo="label+percent",
        textfont=dict(size=11),
        hovertemplate="%{label}: %{value}<extra></extra>",
    ))

    fig.update_layout(
        **BASE_LAYOUT,
        height=220,
        legend=dict(orientation="v", font=dict(size=10)),
    )
    return fig


# ── 5. LOAD GAUGE ─────────────────────────────────────────────
def chart_load_gauge(current_load: float, peak_load: float) -> go.Figure:
    """
    Gauge / speedometer showing current load vs peak capacity.
    Colour transitions: blue → orange → red.
    """
    pct   = current_load / peak_load * 100
    color = "#ff3b5c" if pct > 85 else "#ffaa00" if pct > 70 else "#00d4ff"

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=current_load,
        delta=dict(
            reference=peak_load * 0.70,
            valueformat=".1f",
            increasing=dict(color="#ff3b5c"),
            decreasing=dict(color="#00ff88"),
        ),
        number=dict(
            suffix=" MW",
            font=dict(size=22, color="#e8f4fc", family="Rajdhani, sans-serif"),
        ),
        gauge=dict(
            axis=dict(
                range=[0, peak_load],
                tickfont=dict(size=9, color="#4a6a7a"),
                tickcolor="#0d2640",
                nticks=5,
            ),
            bar=dict(color=color, thickness=0.28),
            bgcolor="#080f1a",
            bordercolor="#0d2640",
            borderwidth=1,
            steps=[
                dict(range=[0,             peak_load * 0.70], color="rgba(0,212,255,0.06)"),
                dict(range=[peak_load*0.70, peak_load * 0.85], color="rgba(255,170,0,0.06)"),
                dict(range=[peak_load*0.85, peak_load],        color="rgba(255,59,92,0.06)"),
            ],
            threshold=dict(
                line=dict(color="#ff3b5c", width=2),
                thickness=0.80,
                value=peak_load * 0.90,
            ),
        ),
    ))

    fig.update_layout(
        paper_bgcolor="#0a1525",
        font=dict(color="#c0d8e8", family="Exo 2, sans-serif"),
        height=190,
        margin=dict(l=20, r=20, t=15, b=10),
    )
    return fig
