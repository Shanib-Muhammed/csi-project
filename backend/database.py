"""Small local SQLite event store."""
from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Any

class EventStore:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT NOT NULL, status TEXT NOT NULL,
                signal_score REAL NOT NULL, motion_score REAL NOT NULL,
                rssi INTEGER NOT NULL, channel INTEGER NOT NULL
            )""")

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        return db

    def add_event(self, event_type: str, state: dict[str, Any]) -> None:
        with self._connect() as db:
            db.execute(
                "INSERT INTO events(event_type,status,signal_score,motion_score,rssi,channel) VALUES(?,?,?,?,?,?)",
                (event_type, state.get("status", "UNKNOWN"),
                 float(state.get("signal_score", 0)), float(state.get("motion_score", 0)),
                 int(state.get("rssi", 0)), int(state.get("channel", 0))),
            )

    def recent(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
            return [dict(row) for row in rows]
