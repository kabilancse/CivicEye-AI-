"""
SQLite database layer for CivicEye AI+.

Tables
------
users            : authentication + role-based access
interventions    : Action Center workflow (NOT a complaint/ticket system —
                    an intervention is created by an authorized org/admin
                    in response to an identified pattern, with an evidence
                    trail and a progress/outcome log)
civic_items      : Citizen Mode content (local info, ongoing initiatives,
                    verified completed initiatives) — always tagged with
                    source/date/type/status so nothing is presented as
                    live news when it is model-derived
pattern_cache    : optional cache of the last computed Social Radar run,
                    so Action Center can reference a stable pattern id
"""

import sqlite3
from contextlib import contextmanager

from config import Config


def get_connection():
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def db_cursor(commit=False):
    conn = get_connection()
    try:
        cur = conn.cursor()
        yield cur
        if commit:
            conn.commit()
    finally:
        conn.close()


def init_db():
    """Create all tables if they do not already exist. Safe to call every startup."""
    with db_cursor(commit=True) as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN
                    ('citizen','researcher','organization','platform_admin','data_admin')),
                organization_name TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS auth_tokens (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                expires_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS interventions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                problem_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                area TEXT,
                organization_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'proposed' CHECK(status IN
                    ('proposed','in_progress','completed','verified')),
                evidence TEXT,
                progress_notes TEXT,
                outcome TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (organization_id) REFERENCES users(id)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS civic_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                area TEXT,
                item_type TEXT NOT NULL CHECK(item_type IN
                    ('local_info','identified_pattern','ongoing_initiative','completed_initiative')),
                source TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                item_date TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS pattern_cache (
                id TEXT PRIMARY KEY,
                title TEXT,
                area TEXT,
                severity TEXT,
                indicators TEXT,
                explanation TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)


def seed_demo_civic_items():
    """Populate a handful of demo Citizen Mode items if the table is empty."""
    with db_cursor() as cur:
        cur.execute("SELECT COUNT(*) AS c FROM civic_items")
        count = cur.fetchone()["c"]
    if count > 0:
        return

    demo_items = [
        (
            "School transport route expansion under review",
            "Local authority is reviewing bus route coverage for rural school zones "
            "after data flagged low transport access in several areas.",
            "Kanchipuram Rural South", "ongoing_initiative", "CivicEye Demo Seed",
            "in_progress",
        ),
        (
            "Free internet access points installed in 3 panchayats",
            "Community internet kiosks were installed as a completed pilot initiative "
            "in response to low connectivity indicators.",
            "Sriperumbudur", "completed_initiative", "CivicEye Demo Seed", "verified",
        ),
        (
            "Attendance pattern under observation",
            "Model-based analysis flagged an association between transport access and "
            "attendance in this area. This is a potential pattern, not a confirmed cause.",
            "Walajabad", "identified_pattern", "CivicEye Social Radar (demo run)", "active",
        ),
        (
            "District education helpline available",
            "General local civic information for residents seeking school enrollment support.",
            "Kanchipuram Urban", "local_info", "CivicEye Demo Seed", "active",
        ),
    ]

    with db_cursor(commit=True) as cur:
        cur.executemany(
            """INSERT INTO civic_items (title, description, area, item_type, source, status)
               VALUES (?, ?, ?, ?, ?, ?)""",
            demo_items,
        )
