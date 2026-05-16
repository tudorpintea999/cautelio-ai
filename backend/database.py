import os
import secrets
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "cautelio.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            email      TEXT UNIQUE NOT NULL,
            api_key    TEXT UNIQUE NOT NULL,
            plan       TEXT NOT NULL DEFAULT 'free',
            status     TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()


def create_user(email: str) -> dict:
    api_key = "caut_" + secrets.token_urlsafe(24)
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (email, api_key) VALUES (?, ?)",
            (email, api_key),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
        return dict(row)
    finally:
        conn.close()


def get_user_by_key(api_key: str) -> dict | None:
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE api_key = ?", (api_key,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_user_by_email(email: str) -> dict | None:
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def activate_user(email: str):
    conn = get_db()
    try:
        conn.execute(
            "UPDATE users SET plan = 'paid', status = 'active' WHERE email = ?",
            (email,),
        )
        conn.commit()
    finally:
        conn.close()


def deactivate_user(email: str):
    conn = get_db()
    try:
        conn.execute(
            "UPDATE users SET status = 'cancelled' WHERE email = ?",
            (email,),
        )
        conn.commit()
    finally:
        conn.close()
