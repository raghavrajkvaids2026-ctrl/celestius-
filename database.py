"""SQLite layer. Plain sqlite3 so every line is easy to explain."""
import os
import sqlite3

DB_PATH = os.environ.get("DB_PATH", "registrations.db")


def get_connection() -> sqlite3.Connection:
    # isolation_level=None -> we control transactions manually (BEGIN IMMEDIATE)
    conn = sqlite3.connect(DB_PATH, isolation_level=None, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS registrations (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                name          TEXT NOT NULL,
                email         TEXT NOT NULL UNIQUE COLLATE NOCASE,
                college       TEXT,
                department    TEXT,
                registered_at TEXT NOT NULL
            )
            """
        )
    finally:
        conn.close()
