
import sqlite3
import json
from pathlib import Path
import pandas as pd

DB_PATH = Path(__file__).resolve().parent.parent / "dealradar.sqlite3"


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with connect() as con:
        con.execute("""
        CREATE TABLE IF NOT EXISTS listings (
            listing_id TEXT PRIMARY KEY,
            product_name TEXT,
            category TEXT,
            platform TEXT,
            condition TEXT,
            model_age_years REAL,
            buy_price REAL,
            buy_fees REAL,
            repair_cost REAL,
            resale_price REAL,
            sell_fees REAL,
            outbound_shipping REAL,
            data_origin TEXT,
            listing_url TEXT,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)
        con.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """)


def save_listings(df):
    columns = [
        "listing_id", "product_name", "category", "platform",
        "condition", "model_age_years", "buy_price", "buy_fees",
        "repair_cost", "resale_price", "sell_fees",
        "outbound_shipping", "data_origin", "listing_url", "notes"
    ]

    with connect() as con:
        for _, row in df.iterrows():
            values = []
            for col in columns:
                val = row.get(col, "")
                if pd.isna(val):
                    val = ""
                if col in [
                    "model_age_years", "buy_price", "buy_fees",
                    "repair_cost", "resale_price", "sell_fees",
                    "outbound_shipping"
                ]:
                    try:
                        val = float(val)
                    except (TypeError, ValueError):
                        val = 0.0
                values.append(val)

            placeholders = ",".join(["?"] * len(columns))
            con.execute(
                f"INSERT OR REPLACE INTO listings "
                f"({','.join(columns)}) VALUES ({placeholders})",
                values
            )


def load_listings():
    with connect() as con:
        return pd.read_sql_query(
            "SELECT * FROM listings ORDER BY created_at DESC", con
        )


def save_settings(settings):
    with connect() as con:
        for key, value in settings.items():
            con.execute(
                "INSERT OR REPLACE INTO settings(key,value) VALUES (?,?)",
                (key, json.dumps(value))
            )


def load_settings():
    result = {}
    with connect() as con:
        rows = con.execute("SELECT key,value FROM settings").fetchall()

    for row in rows:
        try:
            result[row["key"]] = json.loads(row["value"])
        except Exception:
            pass

    return result
