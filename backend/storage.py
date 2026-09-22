from __future__ import annotations

import sqlite3
from pathlib import Path


class AuditStore:
    def __init__(self, path: str = "data/algocontrol.db"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS audit (id INTEGER PRIMARY KEY, event TEXT, details TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)")

    def record(self, event: str, details: str) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute("INSERT INTO audit(event, details) VALUES (?, ?)", (event, details))

    def latest(self, limit: int = 25) -> list[dict]:
        with sqlite3.connect(self.path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT id,event,details,created_at FROM audit ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(row) for row in rows]
