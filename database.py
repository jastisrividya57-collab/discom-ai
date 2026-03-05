"""
database.py
-----------
Handles SQLite database: create tables, save users, verify login, log anomalies.
"""

import sqlite3
import hashlib
import os

DB_PATH = "discom.db"


def get_db():
    """Return a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist. Call this once on app start."""
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            email       TEXT    UNIQUE NOT NULL,
            password    TEXT    NOT NULL,
            location    TEXT    NOT NULL,
            created_at  TEXT    DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS anomaly_log (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       INTEGER,
            location      TEXT,
            feeder        TEXT,
            anomaly_type  TEXT,
            severity      TEXT,
            timestamp     TEXT,
            actual_load   REAL,
            forecast_load REAL,
            residual      REAL,
            explanation   TEXT
        )
    """)
    conn.commit()
    conn.close()


def hash_password(password: str) -> str:
    """Return SHA-256 hash of the password."""
    return hashlib.sha256(password.encode()).hexdigest()


def create_user(name: str, email: str, password: str, location: str):
    """
    Insert a new user.
    Returns (user_dict, error_message).
    error_message is None on success.
    """
    try:
        conn = get_db()
        conn.execute(
            "INSERT INTO users (name, email, password, location) VALUES (?, ?, ?, ?)",
            (name, email, hash_password(password), location)
        )
        conn.commit()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()
        return dict(user), None
    except sqlite3.IntegrityError:
        return None, "Email already registered. Please login."


def verify_user(email: str, password: str):
    """
    Check email + password.
    Returns user dict on success, None on failure.
    """
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE email = ? AND password = ?",
        (email, hash_password(password))
    ).fetchone()
    conn.close()
    return dict(user) if user else None


def update_user_location(user_id: int, location: str):
    """Save the updated location for an existing user."""
    conn = get_db()
    conn.execute("UPDATE users SET location = ? WHERE id = ?", (location, user_id))
    conn.commit()
    conn.close()


def save_anomalies(user_id: int, location: str, feeder: str, anomalies: list):
    """Persist High / Critical anomalies to the log table."""
    conn = get_db()
    for a in anomalies:
        if a["severity"] in ("Critical", "High"):
            conn.execute("""
                INSERT INTO anomaly_log
                    (user_id, location, feeder, anomaly_type, severity,
                     timestamp, actual_load, forecast_load, residual, explanation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, location, feeder,
                a["type"], a["severity"], a["timestamp"],
                a["actual"], a["forecast"], a["residual"], a["explanation"]
            ))
    conn.commit()
    conn.close()


def get_anomaly_history(user_id: int) -> list:
    """Return the last 30 logged anomalies for this user."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM anomaly_log WHERE user_id = ? ORDER BY id DESC LIMIT 30",
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
