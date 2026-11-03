import csv
import sqlite3
from pathlib import Path

from app.settings import DATA_DIR

OUTAGES_SEED_PATH = DATA_DIR / "outages_seed.csv"

SCHEMA = """
CREATE TABLE IF NOT EXISTS outages (
    protocol TEXT PRIMARY KEY,
    neighborhood TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TEXT NOT NULL,
    estimated_restoration TEXT
);
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    neighborhood TEXT NOT NULL,
    kind TEXT NOT NULL,
    street_or_reference TEXT,
    outage_since TEXT,
    opened_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    neighborhood_asks INTEGER NOT NULL,
    pending_message TEXT
);
CREATE TABLE IF NOT EXISTS attendances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    message TEXT NOT NULL,
    triage_result TEXT,
    action TEXT NOT NULL,
    handed_to_human INTEGER NOT NULL,
    handoff_reason TEXT,
    model TEXT NOT NULL,
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    cost_brl REAL,
    latency_seconds REAL NOT NULL
);
"""


def connect(path: str) -> sqlite3.Connection:
    connection = sqlite3.connect(path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    return connection


def seed_outages(connection: sqlite3.Connection, seed_path: Path) -> None:
    with seed_path.open(encoding="utf-8", newline="") as file:
        rows = [
            (
                row["protocol"],
                row["neighborhood"],
                row["status"],
                row["started_at"],
                row["estimated_restoration"] or None,
            )
            for row in csv.DictReader(file)
        ]
    connection.executemany("INSERT INTO outages VALUES (?, ?, ?, ?, ?)", rows)


def initialize(connection: sqlite3.Connection, seed_path: Path = OUTAGES_SEED_PATH) -> None:
    connection.executescript(SCHEMA)
    existing = connection.execute("SELECT COUNT(*) FROM outages").fetchone()[0]
    if existing == 0:
        seed_outages(connection, seed_path)
    connection.commit()
