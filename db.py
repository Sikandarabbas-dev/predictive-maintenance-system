"""
Database connection layer.
Same pattern as the other projects: MySQL in production, automatic
SQLite fallback for zero-setup local demo/testing.
"""

import os
import sqlite3

USE_SQLITE_FALLBACK = os.getenv("USE_SQLITE_FALLBACK", "true").lower() == "true"

MYSQL_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "predictive_maintenance_db"),
}

SQLITE_PATH = os.path.join(os.path.dirname(__file__), "maintenance.db")


def get_connection():
    if not USE_SQLITE_FALLBACK:
        import mysql.connector
        return mysql.connector.connect(**MYSQL_CONFIG)

    try:
        import mysql.connector
        return mysql.connector.connect(**MYSQL_CONFIG)
    except Exception:
        conn = sqlite3.connect(SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        return conn


def init_sqlite_schema():
    conn = sqlite3.connect(SQLITE_PATH)
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS machines (
            machine_id INTEGER PRIMARY KEY AUTOINCREMENT,
            machine_name TEXT NOT NULL,
            machine_type TEXT,
            installed_at TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS sensor_readings (
            reading_id INTEGER PRIMARY KEY AUTOINCREMENT,
            machine_id INTEGER NOT NULL,
            reading_date TEXT NOT NULL,
            runtime_hours REAL NOT NULL,
            temperature REAL NOT NULL,
            vibration REAL NOT NULL,
            pressure REAL NOT NULL,
            failed INTEGER DEFAULT 0,
            FOREIGN KEY (machine_id) REFERENCES machines(machine_id)
        );

        CREATE TABLE IF NOT EXISTS maintenance_alerts (
            alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
            machine_id INTEGER NOT NULL,
            failure_risk REAL NOT NULL,
            risk_level TEXT NOT NULL,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (machine_id) REFERENCES machines(machine_id)
        );
        """
    )
    conn.commit()
    conn.close()


def is_sqlite(conn):
    return isinstance(conn, sqlite3.Connection)
