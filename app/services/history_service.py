"""In-memory query history store."""

from __future__ import annotations

from datetime import datetime
from typing import Any


class HistoryStore:
    """Thread-unsafe in-memory store sufficient for a single-process demo."""

    def __init__(self) -> None:
        self._records: list[dict[str, Any]] = []
        self._counter = 0

    def add(self, record: dict[str, Any]) -> dict[str, Any]:
        self._counter += 1
        entry = {
            "id": self._counter,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            **record,
        }
        self._records.insert(0, entry)
        return entry

    def list(self, search: str | None = None, status: str | None = None) -> list[dict[str, Any]]:
        records = list(self._records)
        if search:
            query = search.lower()
            records = [r for r in records if query in (r.get("user_query") or "").lower()]
        if status:
            records = [r for r in records if r.get("status") == status]
        return records

    def clear(self) -> None:
        self._records.clear()

    def get(self, history_id: int) -> dict[str, Any] | None:
        for record in self._records:
            if record.get("id") == history_id:
                return record
        return None


history_store = HistoryStore()
