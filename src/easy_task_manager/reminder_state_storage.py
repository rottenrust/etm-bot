"""Persistent state for daily reminder slots."""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict


class JsonReminderStateStorage:
    """Store processed daily reminder slots in a local JSON file."""

    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path

    def initialize(self) -> None:
        """Create an empty reminder state file when it does not exist yet."""
        if self.file_path.exists():
            return
        self._write_raw_state({})

    def is_daily_slot_processed(self, day: date, slot_name: str) -> bool:
        """Return True when a daily reminder slot was already processed."""
        day_state = self._read_raw_state().get(day.isoformat())
        if not isinstance(day_state, dict):
            return False
        return slot_name in day_state

    def mark_daily_slot_processed(
        self,
        day: date,
        slot_name: str,
        processed_at: datetime,
    ) -> None:
        """Mark a daily reminder slot as processed."""
        state = self._read_raw_state()
        day_key = day.isoformat()
        day_state = state.setdefault(day_key, {})
        if not isinstance(day_state, dict):
            day_state = {}
            state[day_key] = day_state
        day_state[slot_name] = processed_at.isoformat()
        self._write_raw_state(state)

    def _read_raw_state(self) -> Dict[str, Any]:
        if not self.file_path.exists():
            return {}
        with self.file_path.open("r", encoding="utf-8") as source:
            loaded = json.load(source)
        if not isinstance(loaded, dict):
            return {}
        return loaded

    def _write_raw_state(self, state: Dict[str, Any]) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        with self.file_path.open("w", encoding="utf-8") as destination:
            json.dump(state, destination, ensure_ascii=False, indent=2)
