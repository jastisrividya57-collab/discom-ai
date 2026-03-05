"""
app.py  ─  DISCOM AI — Main Streamlit Application
══════════════════════════════════════════════════
AI-Driven Electricity Demand Forecasting &
Explainable Anomaly Detection for DISCOMs

Project   : Final Year Project — CSE Batch 07
Institute : KKR & KSR Institute of Technology & Sciences, Guntur
Guide     : Mrs. R. Madhuri Devi, Assistant Professor

How to run
──────────
    streamlit run app.py

What each file does
───────────────────
    app.py        — Main entry point; login / signup / dashboard pages
    config.py     — Location + DISCOM master data
    database.py   — SQLite helpers (users, anomaly log)
    ai_engine.py  — N-BEATS forecasting + anomaly detection + metrics
    charts.py     — Plotly chart functions
    styles.py     — All CSS injected once at startup
"""

# ── Standard library ──────────────────────────────────────────
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# ── Streamlit ─────────────────────────────────────────────────
import streamlit as st

# ── Project modules ───────────────────────────────────────────
from config   import LOCATIONS, LOCATION_NAMES
from database import (
    init_db, create_user, verify_user,
    update_user_location, save_anomalies, get_anomaly_history,
)
from ai_engine import (
    generate_load_data, nbeats_forecast,
    detect_anomalies, compute_metrics,
)
from charts import (
    chart_actual_vs_forecast, chart_residual,
    chart_forecast_12h, chart_anomaly_donut, chart_load_gauge,
)
from styles import inject_css


# ─────────────────────────────────────────────────────────────
# PAGE CONFIGURATION  (must be the very first Streamlit call)
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DISCOM AI Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject custom CSS
inject_css()

# ─────────────────────────────────────────────────────────────
# INITIALISE DATABASE + SESSION STATE
# ─────────────────────────────────────────────────────────────
init_db()   # creates discom.db + tables if they don't exist

for key, default in [
    ("logged_in",    False),
    ("user",         None),
    ("page",         "login"),
    ("login_error",  ""),
    ("signup_error", ""),
]:
    if key not in st.session_state:
        st.session_state[key] = default


# ─────────────────────────────────────────────────────────────
# ANALYTICS ENGINE  (cached — re-runs only when inputs change)
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=60, show_spinner=False)
def run_analytics(location: str, feeder_idx: int) -> dict:
    """
    Full pipeline:
      1. Generate 72 h of simulated load data
      2. Run N-BEATS forecast on 60-h history window
      3. Detect anomalies on the latest 48-h window
      4. Compute accuracy metrics
      5. Build 12-h ahead forecast
    Returns a single dict consumed by all chart functions.
    """
    np.random.seed(abs(hash(location + str(feeder_idx))) % 9999)

    info   = LOCATIONS[location]
    feeder = info["feeders"][feeder_idx % len(info["feeders"])]

    # Step 1 — raw data (72 hours)
    raw      = generate_load_data(location, info, hours=72)
    all_load = [d["actual_load"] for d in raw]
    actual   = all_load[24:]                          # last 48 h displayed
    ts       = [d["timestamp"] for d in raw[24:]]

    # Step 2 — N-BEATS forecast on first 60 h
    fc_all   = nbeats_forecast(all_load[:60], steps=60)
    forecast = fc_all[12:]                            # align with 48-h window

    # Step 3 — anomaly detection
    anomalies = detect_anomalies(actual, forecast, ts)

    # Step 4 — metrics
    metrics = compute_metrics(actual, forecast)

    # Step 5 — next 12 h forecast
    next_ts  = [
        (datetime.now() + timedelta(hours=i + 1)).strftime("%H:%M")
        for i in range(12)
    ]
    next_val = nbeats_forecast(actual, steps=12)

    return {
        "feeder":       feeder,
        "discom":       info["discom"],
        "timestamps":   ts,
        "actual":       actual,
        "forecast":     forecast,
        "anomalies":    anomalies,
        "metrics":      metrics,
        "next_ts":      next_ts,
        "next_val":     next_val,
        "current_load": actual[-1],
        "peak":         info["peak"],
        "base":         info["base"],
        "load_factor":  round(
            (sum(actual) / len(actual)) / info["peak"] * 100, 1
        ),
    }


# ─────────────────────────────────────────────────────────────
# HTML HELPERS
# ─────────────────────────────────────────────────────────────
SEV_CLASS  = {
    "Critical": "chip-critical",
    "High":     "chip-high",
    "Medium":   "chip-medium",
    "Low":      "chip-low",
}
TYPE_CLASS = {
    "Load Spike":         "chip-spike",
    "Load Drop":          "chip-drop",
    "Demand Drift":       "chip-drift",
    "Meter Fault":        "chip-fault",
    "Communication Loss": "chip-comm",
}


def metric_card_html(icon, value, unit, label, badge_text, badge_class, color="blue") -> str:
    """Return HTML for one KPI card."""
    return f"""
    <div class="metric-card {color}">
      <div class="metric-icon">{icon}</div>
      <div class="metric-value">{value}<span class="metric-unit"> {unit}</span></div>
      <div class="metric-label">{label}</div>
      <span class="metric-badge {badge_class}">{badge_text}</span>
    </div>"""


def anomaly_table_html(anomalies: list) -> str:
    """Return full HTML for the anomaly table."""
    if not anomalies:
        return (
            '<div style="text-align:center;padding:40px;color:#00ff88;font-size:14px">'
            "✔ No anomalies detected in this 48-hour window</div>"
        )

    rows = ""
    for a in anomalies:
        sign  = "+" if a["residual"] > 0 else ""
        rcol  = "#ff4466" if a["residual"] > 0 else "#ff8800"
        tc    = TYPE_CLASS.get(a["type"], "")
        sc    = SEV_CLASS.get(a["severity"], "")
        rows += f"""
        <tr>
          <td style="font-family:'Share Tech Mono',monospace;font-size:11px;
                     white-space:nowrap">{a['timestamp']}</td>
          <td><span class="chip {tc}">{a['type']}</span></td>
          <td><span class="chip {sc}">{a['severity']}</span></td>
          <td style="font-family:'Share Tech Mono',monospace">{a['actual']}</td>
          <td style="font-family:'Share Tech Mono',monospace">{a['forecast']}</td>
          <td style="font-family:'Share Tech Mono',monospace;
                     color:{rcol}">{sign}{a['residual']}</td>
          <td style="font-family:'Share Tech Mono',monospace">{a['pct_deviation']}%</td>
          <td style="font-size:11px;color:#8aa0b0;line-height:1.5;
                     max-width:260px">{a['explanation']}</td>
        </tr>"""

    return f"""
    <table class="anom-table">
      <thead><tr>
        <th>Timestamp</th><th>Type</th><th>Severity</th>
        <th>Actual (MW)</th><th>Forecast (MW)</th>
        <th>Residual</th><th>Dev %</th><th>AI Explanation</th>
      </tr></thead>
      <tbody>{rows}</tbody>
    </table>"""


# ═════════════════════════════════════════════════════════════
#  PAGE 1 — LOGIN
# ═════════════════════════════════════════════════════════════
def page_login():
    # Logo
    st.markdown("""
    <div style="text-align:center; margin-top:40px; margin-bottom:32px">
      <div style="font-size:52px; margin-bottom:8px">⚡</div>
      <div style="font-family:'Rajdhani',sans-serif; font-size:32px; font-weight:700;
                  letter-spacing:4px; background:linear-gradient(90deg,#00d4ff,#66e8ff);
                  -webkit-background-clip:text; -webkit-text-fill-color:transparent">
        DISCOM AI
      </div>
      <div style="font-size:11px; color:#4a6a7a; letter-spacing:2px;
                  text-transform:uppercase; margin-top:4px">
        Electricity Intelligence Platform
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Centre the form
    _, col, _ = st.columns([1, 1.4, 1])
    with col:
        st.markdown('<div class="auth-card"><div class="auth-title">Operator Login</div>',
                    unsafe_allow_html=True)

        if st.session_state.login_error:
            st.error(st.session_state.login_error)

        email    = st.text_input("Email Address", placeholder="operator@discom.gov.in",
                                 key="login_email")
        password = st.text_input("Password", type="password",
                                 placeholder="Enter your password", key="login_pw")

        if st.button("▶  Login to Dashboard", key="btn_login"):
            if not email or not password:
                st.session_state.login_error = "Please enter your email and password."
                st.rerun()

            user = verify_user(email.strip().lower(), password)
            if user:
                st.session_state.logged_in   = True
                st.session_state.user        = user
                st.session_state.login_error = ""
                st.session_state.page        = "dashboard"
                st.rerun()
            else:
                st.session_state.login_error = "Invalid email or password. Please try again."
                st.rerun()

        st.markdown(
            '<div style="text-align:center; margin-top:20px; font-size:13px; color:#4a6a7a">'
            "Don't have an account?</div>",
            unsafe_allow_html=True,
        )
        if st.button("→  Register Here", key="btn_go_signup"):
            st.session_state.page        = "signup"
            st.session_state.login_error = ""
            st.rerun()

        st.markdown("""
        <div style="margin-top:20px; padding-top:16px; border-top:1px solid #0d2640;
                    font-size:11px; color:#2a4a5a; text-align:center; letter-spacing:1px">
          ● SYSTEM ONLINE · KITS CSE · AI MONITORING ACTIVE
        </div></div>
        """, unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════
#  PAGE 2 — SIGN UP
# ═════════════════════════════════════════════════════════════
def page_signup():
    st.markdown("""
    <div style="text-align:center; margin-top:30px; margin-bottom:24px">
      <div style="font-size:44px">⚡</div>
      <div style="font-family:'Rajdhani',sans-serif; font-size:28px; font-weight:700;
                  letter-spacing:4px; background:linear-gradient(90deg,#00d4ff,#66e8ff);
                  -webkit-background-clip:text; -webkit-text-fill-color:transparent">
        DISCOM AI
      </div>
      <div style="font-size:11px; color:#4a6a7a; letter-spacing:2px; text-transform:uppercase">
        Operator Registration
      </div>
    </div>
    """, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 1.8, 1])
    with col:
        st.markdown('<div class="auth-card"><div class="auth-title">Create Account</div>',
                    unsafe_allow_html=True)

        if st.session_state.signup_error:
            st.error(st.session_state.signup_error)

        c1, c2 = st.columns(2)
        with c1:
            name  = st.text_input("Full Name",     placeholder="Ravi Kumar",      key="su_name")
        with c2:
            email = st.text_input("Email Address", placeholder="you@discom.in",   key="su_email")

        c3, c4 = st.columns(2)
        with c3:
            pw1 = st.text_input("Password",         type="password",
                                placeholder="Min. 6 characters", key="su_pw1")
        with c4:
            pw2 = st.text_input("Confirm Password", type="password",
                                placeholder="Repeat password",   key="su_pw2")

        # Location selector
        st.markdown("""
        <div style="font-size:11px; font-weight:500; letter-spacing:2px;
                    text-transform:uppercase; color:#4a6a7a;
                    margin-top:8px; margin-bottom:6px">
          📍 Select Your Service Location
        </div>
        <div style="font-size:11px; color:#3a5a6a; margin-bottom:10px">
          Analytics will be personalised for your region's DISCOM data.
        </div>
        """, unsafe_allow_html=True)

        location = st.selectbox("Location", LOCATION_NAMES,
                                key="su_location", label_visibility="collapsed")

        # Show location info card
        if location:
            info = LOCATIONS[location]
            st.markdown(f"""
            <div style="background:rgba(0,212,255,0.05); border:1px solid rgba(0,212,255,0.15);
                        border-radius:8px; padding:10px 14px; font-size:12px;
                        display:flex; gap:24px; margin-bottom:14px; flex-wrap:wrap">
              <span>🏢 <b style="color:#c0d8e8">{info['discom']}</b></span>
              <span>📍 {info['state']}</span>
              <span>⚡ Peak: {info['peak']} MW</span>
              <span>📊 Base: {info['base']} MW</span>
            </div>
            """, unsafe_allow_html=True)

        if st.button("▶  Create Account & Login", key="btn_signup"):
            # Validation
            errors = []
            if not name.strip():   errors.append("Name is required.")
            if not email.strip():  errors.append("Email is required.")
            if len(pw1) < 6:       errors.append("Password must be at least 6 characters.")
            if pw1 != pw2:         errors.append("Passwords do not match.")
            if not location:       errors.append("Please select a location.")

            if errors:
                st.session_state.signup_error = "  |  ".join(errors)
                st.rerun()

            user, err = create_user(name.strip(), email.strip().lower(), pw1, location)
            if err:
                st.session_state.signup_error = err
                st.rerun()

            # Auto-login after signup
            st.session_state.logged_in    = True
            st.session_state.user         = user
            st.session_state.signup_error = ""
            st.session_state.page         = "dashboard"
            st.rerun()

        if st.button("← Back to Login", key="btn_back"):
            st.session_state.page         = "login"
            st.session_state.signup_error = ""
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════
#  PAGE 3 — DASHBOARD
# ═════════════════════════════════════════════════════════════
def page_dashboard():
    user     = st.session_state.user
    location = user["location"]

    # ── SIDEBAR ──────────────────────────────────────────────
    with st.sidebar:
        st.markdown(f"""
        <div style="padding:16px 8px 20px; border-bottom:1px solid #0d2640; margin-bottom:16px">
          <div style="font-family:'Rajdhani',sans-serif; font-size:20px; font-weight:700;
                      letter-spacing:3px; color:#00d4ff">⚡ DISCOM AI</div>
          <div style="font-size:10px; color:#4a6a7a; letter-spacing:2px;
                      text-transform:uppercase; margin-top:2px">KITS CSE · Batch 07</div>
        </div>
        <div style="padding:0 8px 12px">
          <div style="font-size:10px; letter-spacing:2px; text-transform:uppercase;
                      color:#4a6a7a; border-left:2px solid #00d4ff;
                      padding-left:10px; margin-bottom:8px">Operator</div>
          <div style="font-size:13px; color:#c0d8e8">👤 {user['name']}</div>
          <div style="font-size:11px; color:#4a6a7a; margin-top:2px">{user['email']}</div>
        </div>
        """, unsafe_allow_html=True)

        # Location switcher
        st.markdown(
            '<div style="font-size:10px; letter-spacing:2px; text-transform:uppercase; '
            'color:#4a6a7a; border-left:2px solid #00d4ff; padding-left:10px; '
            'margin:0 8px 8px">📍 Location</div>',
            unsafe_allow_html=True,
        )
        new_loc = st.selectbox(
            "Location",
            LOCATION_NAMES,
            index=LOCATION_NAMES.index(location),
            key="sb_location",
            label_visibility="collapsed",
        )
        if new_loc != location:
            update_user_location(user["id"], new_loc)
            st.session_state.user["location"] = new_loc
            st.rerun()

        location = new_loc
        info     = LOCATIONS[location]

        # Feeder selector
        st.markdown(
            '<div style="font-size:10px; letter-spacing:2px; text-transform:uppercase; '
            'color:#4a6a7a; border-left:2px solid #00d4ff; padding-left:10px; '
            'margin:16px 8px 8px">⚡ Feeder</div>',
            unsafe_allow_html=True,
        )
        feeder_name = st.radio(
            "Feeder", info["feeders"],
            key="sb_feeder", label_visibility="collapsed",
        )
        feeder_idx = info["feeders"].index(feeder_name)

        # System info box
        st.markdown(f"""
        <div style="margin:20px 8px 0; background:rgba(0,255,136,0.05);
                    border:1px solid rgba(0,255,136,0.15); border-radius:8px; padding:14px">
          <div style="font-size:10px; letter-spacing:2px; text-transform:uppercase;
                      color:#00ff88; margin-bottom:10px">⚙ System Info</div>
          <div style="font-size:12px; color:#4a6a7a; line-height:2">
            DISCOM: <span style="color:#c0d8e8">{info['discom']}</span><br>
            State: <span style="color:#c0d8e8">{info['state']}</span><br>
            Peak Load: <span style="color:#c0d8e8">{info['peak']} MW</span><br>
            Base Load: <span style="color:#c0d8e8">{info['base']} MW</span><br>
            AI Model: <span style="color:#00ff88">N-BEATS</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚪  Logout", key="btn_logout"):
            st.session_state.logged_in    = False
            st.session_state.user         = None
            st.session_state.page         = "login"
            st.session_state.login_error  = ""
            st.session_state.signup_error = ""
            st.rerun()

    # ── HEADER ───────────────────────────────────────────────
    now_str = datetime.now().strftime("%d %b %Y  ·  %H:%M:%S")
    st.markdown(f"""
    <div class="top-header">
      <div>
        <div class="brand-title">⚡ DISCOM AI DASHBOARD</div>
        <div class="brand-sub">
          AI-Driven Electricity Demand Forecasting &amp;
          Explainable Anomaly Detection &nbsp;·&nbsp; {location}
        </div>
      </div>
      <span class="live-badge">● LIVE &nbsp; {now_str}</span>
    </div>
    """, unsafe_allow_html=True)

    # ── RUN ANALYTICS ────────────────────────────────────────
    with st.spinner("Running AI forecasting engine …"):
        d = run_analytics(location, feeder_idx)

    # ── ALERT BANNER ─────────────────────────────────────────
    critical = [a for a in d["anomalies"] if a["severity"] in ("Critical", "High")]
    if critical:
        a0 = critical[0]
        st.markdown(
            f'<div class="alert-critical">🚨 <strong>ALERT [{a0["severity"].upper()}]'
            f' — {a0["type"]}</strong><br>{a0["explanation"]}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="alert-ok">'
            "✔ All feeders operating within normal parameters — No critical anomalies detected"
            "</div>",
            unsafe_allow_html=True,
        )

    # ── KPI CARDS ────────────────────────────────────────────
    load_pct = d["current_load"] / d["peak"] * 100
    lb_text  = "CRITICAL" if load_pct > 85 else "HIGH" if load_pct > 70 else "NORMAL"
    lb_class = "badge-danger" if load_pct > 85 else "badge-warn" if load_pct > 70 else "badge-good"

    nc = len([a for a in d["anomalies"] if a["severity"] == "Critical"])
    nh = len([a for a in d["anomalies"] if a["severity"] == "High"])
    ab_text  = "CRITICAL" if nc > 0 else "HIGH ALERT" if nh > 0 else "MONITORING"
    ab_class = "badge-danger" if nc > 0 else "badge-warn" if nh > 0 else "badge-good"

    lf_class = "badge-warn" if d["load_factor"] > 75 else "badge-good"

    kpi_cols = st.columns(5)
    kpi_data = [
        ("⚡", d["current_load"],           "MW", "Current Load",     lb_text,              lb_class,  "blue"),
        ("🎯", d["metrics"]["accuracy"],    "%",  "Forecast Accuracy","N-BEATS MODEL",       "badge-good","green"),
        ("⚠",  len(d["anomalies"]),         "",   "Anomalies (48h)",  ab_text,               ab_class,  "orange"),
        ("📊", d["load_factor"],            "%",  "Load Factor",      "HEALTHY" if d["load_factor"]<75 else "HIGH", lf_class, "yellow"),
        ("📡", d["metrics"]["rmse"],        "MW", "RMSE Error",       f"MAE = {d['metrics']['mae']} MW","badge-good","purple"),
    ]
    for col, (icon, val, unit, label, badge, bcls, color) in zip(kpi_cols, kpi_data):
        with col:
            st.markdown(metric_card_html(icon, val, unit, label, badge, bcls, color),
                        unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── MAIN CHART: Actual vs Forecast ───────────────────────
    st.markdown(
        '<div class="chart-card">'
        '<div class="chart-title">⚡ Actual Load vs N-BEATS Forecast — 48-Hour Window'
        f'&nbsp;&nbsp;<span style="color:#4a6a7a;font-size:12px">Feeder: {d["feeder"]}</span>'
        "</div>",
        unsafe_allow_html=True,
    )
    st.plotly_chart(chart_actual_vs_forecast(d), use_container_width=True,
                    config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

    # ── ROW 2: Residual | 12h Forecast | Donut ───────────────
    col_a, col_b, col_c = st.columns([1.2, 1, 0.85])

    with col_a:
        st.markdown('<div class="chart-card"><div class="chart-title">📈 Residual Analysis (Actual − Forecast)</div>', unsafe_allow_html=True)
        st.plotly_chart(chart_residual(d), use_container_width=True,
                        config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

    with col_b:
        st.markdown('<div class="chart-card"><div class="chart-title">📡 12-Hour Ahead Forecast</div>', unsafe_allow_html=True)
        st.plotly_chart(chart_forecast_12h(d), use_container_width=True,
                        config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

    with col_c:
        st.markdown('<div class="chart-card"><div class="chart-title">🔍 Anomaly Distribution</div>', unsafe_allow_html=True)
        st.plotly_chart(chart_anomaly_donut(d), use_container_width=True,
                        config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

    # ── ROW 3: Gauge + Metrics ────────────────────────────────
    col_g, col_m = st.columns([1, 2])

    with col_g:
        st.markdown('<div class="chart-card"><div class="chart-title">⚡ Load Gauge</div>', unsafe_allow_html=True)
        st.plotly_chart(chart_load_gauge(d["current_load"], d["peak"]),
                        use_container_width=True, config={"displayModeBar": False})
        st.markdown(
            f'<div style="text-align:center;font-size:11px;color:#4a6a7a;'
            f'margin-top:-8px;padding-bottom:4px">Feeder: {d["feeder"]}</div></div>',
            unsafe_allow_html=True,
        )

    with col_m:
        st.markdown('<div class="chart-card"><div class="chart-title">📊 Model Performance Metrics</div>', unsafe_allow_html=True)
        m_cols = st.columns(4)
        for mc, (lbl, val, color) in zip(m_cols, [
            ("Accuracy",  f"{d['metrics']['accuracy']}%", "#00ff88"),
            ("MAE (MW)",  str(d["metrics"]["mae"]),        "#00d4ff"),
            ("RMSE (MW)", str(d["metrics"]["rmse"]),       "#ff6b2b"),
            ("MAPE",      f"{d['metrics']['mape']}%",      "#ffd700"),
        ]):
            with mc:
                st.markdown(f"""
                <div style="text-align:center; background:#080f1a;
                            border:1px solid #0d2640; border-radius:8px; padding:16px 8px">
                  <div style="font-family:'Share Tech Mono',monospace;
                              font-size:22px; color:{color}">{val}</div>
                  <div style="font-size:10px; letter-spacing:2px;
                              text-transform:uppercase; color:#4a6a7a;
                              margin-top:6px">{lbl}</div>
                </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── ANOMALY TABLE ─────────────────────────────────────────
    st.markdown(f"""
    <div class="chart-card">
      <div class="chart-title">
        ⚠ Detected Anomalies — Explainable AI Classification
        <span style="float:right; font-family:'Share Tech Mono',monospace;
                     font-size:13px; color:#ff6b2b">
          {len(d['anomalies'])} ANOMALIES DETECTED
        </span>
      </div>
      {anomaly_table_html(d['anomalies'])}
    </div>
    """, unsafe_allow_html=True)

    # ── ANOMALY HISTORY (collapsible) ─────────────────────────
    with st.expander("📋  Anomaly History — All Sessions", expanded=False):
        history = get_anomaly_history(user["id"])
        if not history:
            st.info("No history yet. High/Critical anomalies are auto-saved here.")
        else:
            df = pd.DataFrame(history)[[
                "timestamp", "location", "feeder",
                "anomaly_type", "severity", "actual_load", "forecast_load"
            ]]
            df.columns = [
                "Timestamp", "Location", "Feeder",
                "Type", "Severity", "Actual (MW)", "Forecast (MW)"
            ]
            st.dataframe(df, use_container_width=True, hide_index=True)

    # Persist anomalies silently
    save_anomalies(user["id"], location, d["feeder"], d["anomalies"])

    # ── FOOTER ───────────────────────────────────────────────
    st.markdown("""
    <div class="footer">
      DISCOM AI &nbsp;·&nbsp; KKR &amp; KSR Institute of Technology &amp; Sciences
      &nbsp;·&nbsp; Department of CSE &nbsp;·&nbsp; Batch 07<br>
      N-BEATS Forecasting &nbsp;·&nbsp;
      Adaptive Quantile Anomaly Detection &nbsp;·&nbsp;
      Explainable AI Classification
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# ROUTER  —  show the right page based on session state
# ─────────────────────────────────────────────────────────────
if not st.session_state.logged_in:
    if st.session_state.page == "signup":
        page_signup()
    else:
        page_login()
else:
    page_dashboard()
