"""
config.py
---------
All static configuration: location data, DISCOM info, feeder names.
Import this in any file that needs location information.
"""

# ── LOCATION MASTER DATA ──────────────────────────────────────
# Each entry has:
#   state   : Indian state name
#   discom  : Distribution company name
#   feeders : List of feeder names (simulated)
#   peak    : Peak demand in MW  (approximate)
#   base    : Base/minimum load in MW
# ─────────────────────────────────────────────────────────────
LOCATIONS = {
    "Guntur": {
        "state":   "Andhra Pradesh",
        "discom":  "APSPDCL",
        "feeders": [
            "Guntur Main Feeder",
            "Brodipet Feeder",
            "Arundelpet Feeder",
        ],
        "peak": 420,
        "base": 280,
    },
    "Vijayawada": {
        "state":   "Andhra Pradesh",
        "discom":  "APSPDCL",
        "feeders": [
            "Vijayawada City Feeder",
            "Benz Circle Feeder",
            "Kanuru Feeder",
        ],
        "peak": 680,
        "base": 450,
    },
    "Visakhapatnam": {
        "state":   "Andhra Pradesh",
        "discom":  "APEPDCL",
        "feeders": [
            "Vizag Port Feeder",
            "MVP Colony Feeder",
            "Gajuwaka Feeder",
        ],
        "peak": 750,
        "base": 500,
    },
    "Hyderabad": {
        "state":   "Telangana",
        "discom":  "TSSPDCL",
        "feeders": [
            "Secunderabad Feeder",
            "Hitech City Feeder",
            "LB Nagar Feeder",
        ],
        "peak": 1200,
        "base": 800,
    },
    "Chennai": {
        "state":   "Tamil Nadu",
        "discom":  "TANGEDCO",
        "feeders": [
            "Anna Nagar Feeder",
            "T Nagar Feeder",
            "Ambattur Feeder",
        ],
        "peak": 1100,
        "base": 720,
    },
    "Bengaluru": {
        "state":   "Karnataka",
        "discom":  "BESCOM",
        "feeders": [
            "Whitefield Feeder",
            "Koramangala Feeder",
            "Hebbal Feeder",
        ],
        "peak": 1350,
        "base": 900,
    },
    "Mumbai": {
        "state":   "Maharashtra",
        "discom":  "MSEDCL",
        "feeders": [
            "Dharavi Feeder",
            "Andheri Feeder",
            "Thane Feeder",
        ],
        "peak": 1800,
        "base": 1200,
    },
    "Delhi": {
        "state":   "Delhi",
        "discom":  "BSES/TPDDL",
        "feeders": [
            "Connaught Place Feeder",
            "Dwarka Feeder",
            "Rohini Feeder",
        ],
        "peak": 2000,
        "base": 1300,
    },
}

# Convenience list for selectbox / radio widgets
LOCATION_NAMES = list(LOCATIONS.keys())
