"""
styles.py
---------
Returns the CSS string injected via st.markdown(..., unsafe_allow_html=True).
Kept in one place so the main app stays clean.
"""

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;600;700&family=Exo+2:wght@300;400;500;600&family=Share+Tech+Mono&display=swap');

/* ── Hide default Streamlit chrome ── */
#MainMenu         { visibility: hidden; }
footer            { visibility: hidden; }
header            { visibility: hidden; }
.stDeployButton   { display: none; }

/* ── App background ── */
.stApp {
    background: #030810;
    font-family: 'Exo 2', sans-serif;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #080f1a !important;
    border-right: 1px solid #0d2640;
}
[data-testid="stSidebar"] * { color: #c0d8e8 !important; }

/* ── Top header bar ── */
.top-header {
    background: linear-gradient(90deg, #080f1a, #0a1525);
    border: 1px solid #0d2640;
    border-radius: 12px;
    padding: 16px 24px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.brand-title {
    font-family: 'Rajdhani', sans-serif;
    font-size: 26px;
    font-weight: 700;
    letter-spacing: 4px;
    background: linear-gradient(90deg, #00d4ff, #66e8ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.brand-sub {
    font-size: 11px;
    color: #4a6a7a;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-top: 2px;
}
.live-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(0,255,136,0.08);
    border: 1px solid rgba(0,255,136,0.2);
    border-radius: 20px;
    padding: 6px 14px;
    font-size: 12px;
    color: #00ff88;
    letter-spacing: 2px;
    font-family: 'Share Tech Mono', monospace;
}

/* ── KPI / Metric cards ── */
.metric-card {
    background: #0a1525;
    border: 1px solid #0d2640;
    border-radius: 12px;
    padding: 18px 20px;
    position: relative;
    overflow: hidden;
    height: 115px;
    transition: border-color 0.3s;
}
.metric-card:hover { border-color: #1a3d60; }
.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
}
.metric-card.blue::before   { background: linear-gradient(90deg, #00d4ff, transparent); }
.metric-card.green::before  { background: linear-gradient(90deg, #00ff88, transparent); }
.metric-card.orange::before { background: linear-gradient(90deg, #ff6b2b, transparent); }
.metric-card.yellow::before { background: linear-gradient(90deg, #ffd700, transparent); }
.metric-card.purple::before { background: linear-gradient(90deg, #aa66ff, transparent); }

.metric-icon  { font-size: 18px; margin-bottom: 4px; }
.metric-value {
    font-family: 'Rajdhani', sans-serif;
    font-size: 30px;
    font-weight: 700;
    color: #e8f4fc;
    line-height: 1.1;
}
.metric-unit  { font-size: 14px; color: #4a6a7a; font-family: 'Exo 2', sans-serif; }
.metric-label {
    font-size: 10px;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #4a6a7a;
    margin-top: 4px;
}
.metric-badge {
    display: inline-block;
    font-size: 9px;
    padding: 2px 8px;
    border-radius: 20px;
    margin-top: 6px;
    letter-spacing: 1px;
    text-transform: uppercase;
}
.badge-good   { background: rgba(0,255,136,0.10); color: #00ff88; border: 1px solid rgba(0,255,136,0.25); }
.badge-warn   { background: rgba(255,170,0,0.10); color: #ffaa00; border: 1px solid rgba(255,170,0,0.25); }
.badge-danger { background: rgba(255,59,92,0.10); color: #ff3b5c; border: 1px solid rgba(255,59,92,0.25); }

/* ── Chart wrapper ── */
.chart-card {
    background: #0a1525;
    border: 1px solid #0d2640;
    border-radius: 12px;
    padding: 18px 20px;
    margin-bottom: 16px;
}
.chart-title {
    font-family: 'Rajdhani', sans-serif;
    font-size: 14px;
    font-weight: 600;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #c0d8e8;
    margin-bottom: 10px;
    padding-bottom: 10px;
    border-bottom: 1px solid #0d2640;
}

/* ── Alert banners ── */
.alert-critical {
    background: rgba(255,59,92,0.08);
    border: 1px solid rgba(255,59,92,0.25);
    border-left: 3px solid #ff3b5c;
    border-radius: 8px;
    padding: 14px 18px;
    margin-bottom: 16px;
    font-size: 13px;
    color: #c0d8e8;
    line-height: 1.6;
}
.alert-critical strong { color: #ff3b5c; }

.alert-ok {
    background: rgba(0,255,136,0.06);
    border: 1px solid rgba(0,255,136,0.20);
    border-left: 3px solid #00ff88;
    border-radius: 8px;
    padding: 12px 18px;
    margin-bottom: 16px;
    font-size: 13px;
    color: #00ff88;
}

/* ── Anomaly table ── */
.anom-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
    font-family: 'Exo 2', sans-serif;
}
.anom-table th {
    padding: 10px 12px;
    text-align: left;
    font-size: 10px;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #4a6a7a;
    border-bottom: 1px solid #0d2640;
    background: #080f1a;
}
.anom-table td {
    padding: 10px 12px;
    color: #c0d8e8;
    border-bottom: 1px solid rgba(13,38,64,0.6);
    vertical-align: top;
}
.anom-table tr:hover td { background: rgba(0,212,255,0.03); }

/* ── Chips / badges ── */
.chip {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    white-space: nowrap;
}
.chip-critical { background: rgba(255,59,92,0.20);  color: #ff3b5c; border: 1px solid rgba(255,59,92,0.3); }
.chip-high     { background: rgba(255,107,43,0.20); color: #ff6b2b; border: 1px solid rgba(255,107,43,0.3); }
.chip-medium   { background: rgba(255,170,0,0.20);  color: #ffaa00; border: 1px solid rgba(255,170,0,0.3); }
.chip-low      { background: rgba(170,102,255,0.20);color: #aa66ff; border: 1px solid rgba(170,102,255,0.3); }
.chip-spike    { background: rgba(255,68,102,0.15);  color: #ff4466; }
.chip-drop     { background: rgba(255,136,0,0.15);   color: #ff8800; }
.chip-drift    { background: rgba(170,102,255,0.15); color: #aa66ff; }
.chip-fault    { background: rgba(255,59,92,0.15);   color: #ff3b5c; }
.chip-comm     { background: rgba(255,102,0,0.15);   color: #ff6600; }

/* ── Auth pages ── */
.auth-card {
    background: #0a1525;
    border: 1px solid #0d2640;
    border-radius: 16px;
    padding: 36px 40px;
    max-width: 440px;
    margin: 50px auto;
    position: relative;
    overflow: hidden;
}
.auth-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, #00d4ff, transparent);
}
.auth-title {
    font-family: 'Rajdhani', sans-serif;
    font-size: 22px;
    font-weight: 700;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: #c0d8e8;
    text-align: center;
    margin-bottom: 28px;
}

/* ── Streamlit widget overrides ── */
.stTextInput input, .stSelectbox > div > div {
    background: rgba(0,212,255,0.03) !important;
    border: 1px solid #0d2640 !important;
    color: #c0d8e8 !important;
    border-radius: 8px !important;
}
.stTextInput input:focus {
    border-color: #00d4ff !important;
    box-shadow: 0 0 0 3px rgba(0,212,255,0.1) !important;
}
.stButton > button {
    background: linear-gradient(135deg, #00d4ff, #0055cc) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    letter-spacing: 2px !important;
    padding: 10px 24px !important;
    width: 100% !important;
}
.stButton > button:hover {
    box-shadow: 0 8px 25px rgba(0,212,255,0.35) !important;
    transform: translateY(-1px) !important;
}

/* ── Footer ── */
.footer {
    text-align: center;
    padding: 24px 0 8px;
    font-size: 11px;
    color: #2a4a5a;
    border-top: 1px solid #0d2640;
    margin-top: 24px;
    letter-spacing: 1px;
    line-height: 1.8;
}
</style>
"""


def inject_css():
    """Call this once at the top of app.py to inject all styles."""
    import streamlit as st
    st.markdown(CSS, unsafe_allow_html=True)
