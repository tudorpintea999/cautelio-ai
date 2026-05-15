import os
import sqlite3
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), "cautelio.db")


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_key TEXT UNIQUE NOT NULL,
                stripe_customer_id TEXT UNIQUE NOT NULL,
                stripe_subscription_id TEXT UNIQUE NOT NULL,
                email TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def create_subscription(api_key, stripe_customer_id, stripe_subscription_id, email):
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO subscriptions
               (api_key, stripe_customer_id, stripe_subscription_id, email)
               VALUES (?, ?, ?, ?)""",
            (api_key, stripe_customer_id, stripe_subscription_id, email),
        )


def get_by_api_key(api_key: str):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM subscriptions WHERE api_key = ?", (api_key,)
        ).fetchone()


def update_status(stripe_subscription_id: str, status: str):
    with get_conn() as conn:
        conn.execute(
            "UPDATE subscriptions SET status = ? WHERE stripe_subscription_id = ?",
            (status, stripe_subscription_id),
        )
