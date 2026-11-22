"""JSON storage for family task lists."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from easy_task_manager.task_storage import DEFAULT_FAMILY_ID, DEFAULT_TASK_LIST_ID


@dataclass(frozen=True)
class TaskListPreset:
    """Predefined task list family can enable."""

    id: str
    title: str


TASK_LIST_PRESETS = (
    TaskListPreset(id=DEFAULT_TASK_LIST_ID, title="Общий"),
    TaskListPreset(id="shopping", title="Покупки"),
    TaskListPreset(id="home", title="Дом"),
    TaskListPreset(id="dacha", title="Дача"),
    TaskListPreset(id="vacation", title="Отпуск"),
    TaskListPreset(id="health", title="Здоровье"),
    TaskListPreset(id="work", title="Работа"),
)


@dataclass(frozen=True)
class TaskList:
    """Family task list entity persisted in JSON."""

    id: str
    family_id: str
    title: str
    created_at: datetime
    is_archived: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "family_id": self.family_id,
            "title": self.title,
            "created_at": self.created_at.isoformat(),
            "is_archived": self.is_archived,
        }


class JsonTaskListStorage:
    """Task-list storage in a local JSON file."""

    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path

    def initialize(self) -> None:
        """Create an empty task lists file when it does not exist yet."""
        if self.file_path.exists():
            return
        self._write_raw_task_lists([])

    def ensure_default_task_list(self, family_id: str = DEFAULT_FAMILY_ID) -> TaskList:
        """Ensure the family has the default general task list."""
        existing = self.get_task_list(family_id=family_id, list_id=DEFAULT_TASK_LIST_ID)
        if existing is not None:
            return existing
        return self._create_task_list(
            family_id=family_id,
            list_id=DEFAULT_TASK_LIST_ID,
            title=_get_preset_title(DEFAULT_TASK_LIST_ID) or "Общий",
        )

    def list_task_lists_by_family(self, family_id: str) -> List[TaskList]:
        """Return active task lists for a family."""
        self.ensure_default_task_list(family_id=family_id)
        lists = [
            task_list
            for task_list in self._read_task_lists()
            if task_list.family_id == family_id and not task_list.is_archived
        ]
        return sorted(lists, key=_task_list_sort_key)

    def list_missing_presets_by_family(self, family_id: str) -> List[TaskListPreset]:
        """Return presets not yet enabled for a family."""
        enabled_ids = {
            task_list.id for task_list in self.list_task_lists_by_family(family_id=family_id)
        }
        return [preset for preset in TASK_LIST_PRESETS if preset.id not in enabled_ids]

    def get_task_list(self, family_id: str, list_id: str) -> Optional[TaskList]:
        """Return active list by family and id."""
        for task_list in self._read_task_lists():
            if (
                task_list.family_id == family_id
                and task_list.id == list_id
                and not task_list.is_archived
            ):
                return task_list
        return None

    def create_task_list_from_preset(
        self,
        family_id: str,
        preset_id: str,
    ) -> Optional[TaskList]:
        """Enable a predefined task list for a family."""
        title = _get_preset_title(preset_id)
        if title is None:
            return None
        existing = self.get_task_list(family_id=family_id, list_id=preset_id)
        if existing is not None:
            return existing
        return self._create_task_list(family_id=family_id, list_id=preset_id, title=title)

    def delete_task_lists_by_family(self, family_id: str) -> int:
        """Delete every task list belonging to a specific family."""
        raw_task_lists = self._read_raw_task_lists()
        remaining: List[Dict[str, Any]] = []
        deleted_count = 0

        for raw_task_list in raw_task_lists:
            task_list = _task_list_from_dict(raw_task_list)
            if task_list is not None and task_list.family_id == family_id:
                deleted_count += 1
                continue
            remaining.append(raw_task_list)

        if deleted_count:
            self._write_raw_task_lists(remaining)
        return deleted_count

    def _create_task_list(self, family_id: str, list_id: str, title: str) -> TaskList:
        raw_task_lists = self._read_raw_task_lists()
        task_list = TaskList(
            id=list_id,
            family_id=family_id,
            title=title,
            created_at=datetime.now(timezone.utc),
        )
        raw_task_lists.append(task_list.to_dict())
        self._write_raw_task_lists(raw_task_lists)
        return task_list

    def _read_task_lists(self) -> List[TaskList]:
        task_lists: List[TaskList] = []
        for raw_task_list in self._read_raw_task_lists():
            task_list = _task_list_from_dict(raw_task_list)
            if task_list is not None:
                task_lists.append(task_list)
        return task_lists

    def _read_raw_task_lists(self) -> List[Dict[str, Any]]:
        if not self.file_path.exists():
            return []
        with self.file_path.open("r", encoding="utf-8") as source:
            loaded = json.load(source)
        if not isinstance(loaded, list):
            return []
        return [item for item in loaded if isinstance(item, dict)]

    def _write_raw_task_lists(self, task_lists: Sequence[Dict[str, Any]]) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        with self.file_path.open("w", encoding="utf-8") as destination:
            json.dump(list(task_lists), destination, ensure_ascii=False, indent=2)


def _get_preset_title(preset_id: str) -> Optional[str]:
    for preset in TASK_LIST_PRESETS:
        if preset.id == preset_id:
            return preset.title
    return None


def _task_list_from_dict(raw: Dict[str, Any]) -> Optional[TaskList]:
    try:
        list_id = str(raw["id"])
        family_id = str(raw.get("family_id") or DEFAULT_FAMILY_ID)
        title = str(raw["title"])
        created_at = datetime.fromisoformat(str(raw["created_at"]))
        is_archived = bool(raw.get("is_archived", False))
    except (KeyError, TypeError, ValueError):
        return None

    return TaskList(
        id=list_id,
        family_id=family_id,
        title=title,
        created_at=created_at,
        is_archived=is_archived,
    )


def _task_list_sort_key(task_list: TaskList) -> tuple[int, str]:
    if task_list.id == DEFAULT_TASK_LIST_ID:
        return (0, "")
    return (1, task_list.title.lower())
