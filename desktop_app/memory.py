from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import os
import sqlite3
from typing import Iterable


@dataclass
class MemoryItem:
    timestamp: str
    role: str
    content: str


class MemoryStore:
    def __init__(self, root_path: str) -> None:
        self.root_path = self._normalize_path(root_path)
        self._ensure_db()
        self.session_memory: list[MemoryItem] = []

    def _normalize_path(self, path: str) -> str:
        expanded = os.path.expanduser(path.strip())
        return os.path.abspath(expanded)

    def _ensure_db(self) -> None:
        os.makedirs(self.root_path, exist_ok=True)
        with sqlite3.connect(self._db_path()) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    category TEXT NOT NULL,
                    content TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def _db_path(self) -> str:
        return os.path.join(self.root_path, "jarvis_memory.sqlite3")

    def set_root(self, path: str) -> None:
        self.root_path = self._normalize_path(path)
        self._ensure_db()

    def add_session(self, role: str, content: str) -> None:
        item = MemoryItem(timestamp=self._timestamp(), role=role, content=content)
        self.session_memory.append(item)

    def recent_session(self, limit: int = 10) -> list[MemoryItem]:
        return self.session_memory[-limit:]

    def save_long_term(self, category: str, content: str) -> None:
        with sqlite3.connect(self._db_path()) as conn:
            conn.execute(
                "INSERT INTO memories (timestamp, category, content) VALUES (?, ?, ?)",
                (self._timestamp(), category, content),
            )
            conn.commit()

    def fetch_long_term(self, categories: Iterable[str]) -> list[MemoryItem]:
        placeholders = ",".join("?" for _ in categories)
        query = f"SELECT timestamp, category, content FROM memories WHERE category IN ({placeholders})"
        with sqlite3.connect(self._db_path()) as conn:
            rows = conn.execute(query, tuple(categories)).fetchall()
        return [MemoryItem(timestamp=row[0], role=row[1], content=row[2]) for row in rows]

    def _timestamp(self) -> str:
        return datetime.utcnow().isoformat()
