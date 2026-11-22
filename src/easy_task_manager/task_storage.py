"""Simple JSON storage for tasks."""

from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from easy_task_manager.recurrence import (
    get_recurrence_anchor_day,
    normalize_recurrence,
)

DEFAULT_FAMILY_ID = "default"
DEFAULT_TASK_LIST_ID = "general"
_FILE_LOCKS: dict[Path, threading.Lock] = {}
_FILE_LOCKS_GUARD = threading.Lock()


@dataclass(frozen=True)
class Task:
    """Task entity persisted in JSON."""

    id: int
    chat_id: int
    text: str
    deadline: Optional[date]
    created_at: datetime
    deadline_time: Optional[time] = None
    deadline_notified_at: Optional[datetime] = None
    family_id: str = DEFAULT_FAMILY_ID
    list_id: str = DEFAULT_TASK_LIST_ID
    recurrence: Optional[str] = None
    recurrence_anchor_day: Optional[int] = None
    snoozed_until: Optional[datetime] = None
    note: Optional[str] = None
    reminder_enabled: bool = True
    completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "family_id": self.family_id,
            "list_id": self.list_id,
            "chat_id": self.chat_id,
            "created_by_chat_id": self.chat_id,
            "text": self.text,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "deadline_time": self.deadline_time.strftime("%H:%M")
            if self.deadline_time
            else None,
            "created_at": self.created_at.isoformat(),
            "deadline_notified_at": self.deadline_notified_at.isoformat()
            if self.deadline_notified_at
            else None,
            "recurrence": self.recurrence,
            "recurrence_anchor_day": self.recurrence_anchor_day,
            "snoozed_until": self.snoozed_until.isoformat()
            if self.snoozed_until
            else None,
            "note": self.note,
            "reminder_enabled": self.reminder_enabled,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
        }


class JsonTaskStorage:
    """Append-only task storage in a local JSON file."""

    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path

    def initialize(self) -> None:
        """Create an empty tasks file when it does not exist yet."""
        if self.file_path.exists():
            return
        self._write_raw_tasks([])

    def add_task(
        self,
        chat_id: int,
        text: str,
        deadline: Optional[date],
        deadline_time: Optional[time] = None,
        family_id: str = DEFAULT_FAMILY_ID,
        list_id: str = DEFAULT_TASK_LIST_ID,
        recurrence: Optional[str] = None,
        recurrence_anchor_day: Optional[int] = None,
        note: Optional[str] = None,
        reminder_enabled: bool = True,
    ) -> Task:
        tasks = self._read_raw_tasks()
        next_id = max((task["id"] for task in tasks), default=0) + 1
        normalized_recurrence = normalize_recurrence(recurrence) if deadline else None
        normalized_anchor_day = get_recurrence_anchor_day(
            normalized_recurrence,
            deadline,
            anchor_day=recurrence_anchor_day,
        )
        task = Task(
            id=next_id,
            family_id=family_id,
            list_id=list_id,
            chat_id=chat_id,
            text=text,
            deadline=deadline,
            deadline_time=deadline_time if deadline is not None else None,
            created_at=datetime.now(timezone.utc),
            recurrence=normalized_recurrence,
            recurrence_anchor_day=normalized_anchor_day,
            note=note,
            reminder_enabled=reminder_enabled if deadline_time is not None else False,
        )
        tasks.append(task.to_dict())
        self._write_raw_tasks(tasks)
        return task

    def get_task_by_family(
        self,
        family_id: str,
        task_id: int,
    ) -> Optional[Task]:
        """Return task belonging to a specific family."""
        for raw_task in self._read_raw_tasks():
            task = _task_from_dict(raw_task)
            if task is not None and task.family_id == family_id and task.id == task_id:
                return task
        return None

    def list_tasks_by_family(
        self,
        family_id: str,
        now: Optional[datetime] = None,
        include_completed: bool = False,
    ) -> List[Task]:
        """Return family tasks sorted by deadline urgency, then by id."""
        filtered: List[Task] = []
        for raw_task in self._read_raw_tasks():
            task = _task_from_dict(raw_task)
            if task is None:
                continue
            if task.family_id == family_id and _is_visible_to_mini(task, now, include_completed):
                filtered.append(task)
        return sorted(
            filtered,
            key=_task_sort_key,
        )

    def list_tasks_by_family_and_list(
        self,
        family_id: str,
        list_id: str,
        now: Optional[datetime] = None,
        include_completed: bool = False,
    ) -> List[Task]:
        """Return family tasks from a specific task list."""
        filtered: List[Task] = []
        for raw_task in self._read_raw_tasks():
            task = _task_from_dict(raw_task)
            if task is None:
                continue
            if (
                task.family_id == family_id
                and task.list_id == list_id
                and _is_visible_to_mini(task, now, include_completed)
            ):
                filtered.append(task)
        return sorted(
            filtered,
            key=_task_sort_key,
        )

    def list_snoozed_tasks_by_family_and_list(
        self,
        family_id: str,
        list_id: str,
        now: Optional[datetime] = None,
    ) -> List[Task]:
        """Return future-snoozed family tasks from a specific task list."""
        filtered: List[Task] = []
        for raw_task in self._read_raw_tasks():
            task = _task_from_dict(raw_task)
            if task is None:
                continue
            if (
                task.family_id == family_id
                and task.list_id == list_id
                and task.completed_at is None
                and _is_task_snoozed(task, now)
            ):
                filtered.append(task)
        return sorted(filtered, key=_snoozed_task_sort_key)

    def count_tasks_by_family_lists(
        self,
        family_id: str,
        now: Optional[datetime] = None,
    ) -> Dict[str, int]:
        """Return task counts grouped by list id for a family."""
        counts: Dict[str, int] = {}
        for raw_task in self._read_raw_tasks():
            task = _task_from_dict(raw_task)
            if (
                task is None
                or task.family_id != family_id
                or not _is_active_task(task, now)
            ):
                continue
            counts[task.list_id] = counts.get(task.list_id, 0) + 1
        return counts

    def count_snoozed_tasks_by_family_lists(
        self,
        family_id: str,
        now: Optional[datetime] = None,
    ) -> Dict[str, int]:
        """Return future-snoozed task counts grouped by list id for a family."""
        counts: Dict[str, int] = {}
        for raw_task in self._read_raw_tasks():
            task = _task_from_dict(raw_task)
            if (
                task is None
                or task.family_id != family_id
                or task.completed_at is not None
                or not _is_task_snoozed(task, now)
            ):
                continue
            counts[task.list_id] = counts.get(task.list_id, 0) + 1
        return counts

    def list_tasks_by_chat(
        self,
        chat_id: int,
        now: Optional[datetime] = None,
    ) -> List[Task]:
        """Return chat tasks sorted by deadline urgency, then by id."""
        filtered: List[Task] = []
        for raw_task in self._read_raw_tasks():
            task = _task_from_dict(raw_task)
            if task is None:
                continue
            if task.chat_id == chat_id and _is_active_task(task, now):
                filtered.append(task)
        return sorted(
            filtered,
            key=_task_sort_key,
        )

    def list_due_tasks_by_family(self, today: date) -> Dict[str, List[Task]]:
        """Return tasks with reached deadlines grouped by family."""
        grouped: Dict[str, List[Task]] = {}
        for raw_task in self._read_raw_tasks():
            task = _task_from_dict(raw_task)
            if task is None or task.deadline is None or task.completed_at is not None:
                continue
            if task.deadline > today:
                continue
            grouped.setdefault(task.family_id, []).append(task)

        for family_tasks in grouped.values():
            family_tasks.sort(key=_task_sort_key)

        return grouped

    def list_due_tasks_by_chat(self, today: date) -> Dict[int, List[Task]]:
        """Return tasks with reached deadlines grouped by chat."""
        grouped: Dict[int, List[Task]] = {}
        for raw_task in self._read_raw_tasks():
            task = _task_from_dict(raw_task)
            if task is None or task.deadline is None or task.completed_at is not None:
                continue
            if task.deadline > today:
                continue
            grouped.setdefault(task.chat_id, []).append(task)

        for chat_tasks in grouped.values():
            chat_tasks.sort(key=_task_sort_key)

        return grouped

    def list_timed_due_tasks_by_family(self, now: datetime) -> Dict[str, List[Task]]:
        """Return timed tasks with reached exact deadlines grouped by family."""
        local_now = now
        grouped: Dict[str, List[Task]] = {}
        for raw_task in self._read_raw_tasks():
            task = _task_from_dict(raw_task)
            if (
                task is None
                or task.deadline is None
                or task.deadline_time is None
                or task.deadline_notified_at is not None
                or task.completed_at is not None
                or not task.reminder_enabled
            ):
                continue
            if (task.deadline, task.deadline_time) > (local_now.date(), local_now.time()):
                continue
            grouped.setdefault(task.family_id, []).append(task)

        for family_tasks in grouped.values():
            family_tasks.sort(key=_task_sort_key)

        return grouped

    def list_timed_due_tasks_by_chat(self, now: datetime) -> Dict[int, List[Task]]:
        """Return timed tasks with reached exact deadlines grouped by chat."""
        local_now = now
        grouped: Dict[int, List[Task]] = {}
        for raw_task in self._read_raw_tasks():
            task = _task_from_dict(raw_task)
            if (
                task is None
                or task.deadline is None
                or task.deadline_time is None
                or task.deadline_notified_at is not None
                or task.completed_at is not None
                or not task.reminder_enabled
            ):
                continue
            if (task.deadline, task.deadline_time) > (local_now.date(), local_now.time()):
                continue
            grouped.setdefault(task.chat_id, []).append(task)

        for chat_tasks in grouped.values():
            chat_tasks.sort(key=_task_sort_key)

        return grouped

    def get_next_timed_deadline_at(self, now: datetime) -> Optional[datetime]:
        """Return the next pending exact deadline after the provided datetime."""
        local_now = now
        next_deadline_at: Optional[datetime] = None
        for raw_task in self._read_raw_tasks():
            task = _task_from_dict(raw_task)
            if (
                task is None
                or task.deadline is None
                or task.deadline_time is None
                or task.deadline_notified_at is not None
                or task.completed_at is not None
                or not task.reminder_enabled
            ):
                continue
            candidate = datetime.combine(
                task.deadline,
                task.deadline_time,
                tzinfo=local_now.tzinfo,
            )
            if candidate <= local_now:
                continue
            if next_deadline_at is None or candidate < next_deadline_at:
                next_deadline_at = candidate
        return next_deadline_at

    def mark_family_deadline_notifications_sent(
        self,
        family_id: str,
        task_ids: Sequence[int],
        notified_at: datetime,
    ) -> int:
        """Mark exact deadline notifications as sent for family tasks."""
        task_id_set = set(task_ids)
        if not task_id_set:
            return 0

        tasks = self._read_raw_tasks()
        updated_count = 0
        for raw_task in tasks:
            task = _task_from_dict(raw_task)
            if task is None or task.family_id != family_id or task.id not in task_id_set:
                continue
            raw_task["deadline_notified_at"] = notified_at.isoformat()
            updated_count += 1

        if updated_count:
            self._write_raw_tasks(tasks)
        return updated_count

    def mark_deadline_notifications_sent(
        self,
        chat_id: int,
        task_ids: Sequence[int],
        notified_at: datetime,
    ) -> int:
        """Mark exact deadline notifications as sent for chat tasks."""
        task_id_set = set(task_ids)
        if not task_id_set:
            return 0

        tasks = self._read_raw_tasks()
        updated_count = 0
        for raw_task in tasks:
            task = _task_from_dict(raw_task)
            if task is None or task.chat_id != chat_id or task.id not in task_id_set:
                continue
            raw_task["deadline_notified_at"] = notified_at.isoformat()
            updated_count += 1

        if updated_count:
            self._write_raw_tasks(tasks)
        return updated_count

    def update_task_deadline_by_family(
        self,
        family_id: str,
        task_id: int,
        deadline: Optional[date],
        deadline_time: Optional[time] = None,
    ) -> Optional[Task]:
        """Update deadline for a task belonging to a specific family."""
        tasks = self._read_raw_tasks()

        for raw_task in tasks:
            task = _task_from_dict(raw_task)
            if task is None or task.family_id != family_id or task.id != task_id:
                continue

            raw_task["deadline"] = deadline.isoformat() if deadline else None
            raw_task["deadline_time"] = (
                deadline_time.strftime("%H:%M") if deadline and deadline_time else None
            )
            raw_task["deadline_notified_at"] = None
            if deadline is None:
                raw_task["recurrence"] = None
                raw_task["recurrence_anchor_day"] = None
            elif normalize_recurrence(raw_task.get("recurrence")):
                raw_task["recurrence_anchor_day"] = get_recurrence_anchor_day(
                    normalize_recurrence(raw_task.get("recurrence")),
                    deadline,
                )
            self._write_raw_tasks(tasks)
            return _task_from_dict(raw_task)

        return None

    def update_task_by_family(
        self,
        family_id: str,
        task_id: int,
        text: Optional[str] = None,
        deadline: Optional[date] = None,
        deadline_time: Optional[time] = None,
        list_id: Optional[str] = None,
        note: Optional[str] = None,
        reminder_enabled: Optional[bool] = None,
    ) -> Optional[Task]:
        """Update editable fields for a family task."""
        tasks = self._read_raw_tasks()

        for raw_task in tasks:
            task = _task_from_dict(raw_task)
            if task is None or task.family_id != family_id or task.id != task_id:
                continue

            if text is not None:
                raw_task["text"] = text
            if list_id is not None:
                raw_task["list_id"] = list_id
            raw_task["deadline"] = deadline.isoformat() if deadline else None
            raw_task["deadline_time"] = (
                deadline_time.strftime("%H:%M") if deadline and deadline_time else None
            )
            raw_task["deadline_notified_at"] = None
            raw_task["note"] = note
            raw_task["reminder_enabled"] = (
                bool(reminder_enabled) if deadline and deadline_time else False
            )
            if deadline is None:
                raw_task["recurrence"] = None
                raw_task["recurrence_anchor_day"] = None
            elif normalize_recurrence(raw_task.get("recurrence")):
                raw_task["recurrence_anchor_day"] = get_recurrence_anchor_day(
                    normalize_recurrence(raw_task.get("recurrence")),
                    deadline,
                )
            self._write_raw_tasks(tasks)
            return _task_from_dict(raw_task)

        return None

    def update_task_list_by_family(
        self,
        family_id: str,
        task_id: int,
        list_id: str,
    ) -> Optional[Task]:
        """Move a task belonging to a family into another task list."""
        tasks = self._read_raw_tasks()

        for raw_task in tasks:
            task = _task_from_dict(raw_task)
            if task is None or task.family_id != family_id or task.id != task_id:
                continue

            raw_task["list_id"] = list_id
            self._write_raw_tasks(tasks)
            return _task_from_dict(raw_task)

        return None

    def update_task_deadline_by_chat(
        self,
        chat_id: int,
        task_id: int,
        deadline: Optional[date],
        deadline_time: Optional[time] = None,
    ) -> bool:
        """Update deadline for a task belonging to a specific chat."""
        tasks = self._read_raw_tasks()

        for raw_task in tasks:
            task = _task_from_dict(raw_task)
            if task is None or task.chat_id != chat_id or task.id != task_id:
                continue

            raw_task["deadline"] = deadline.isoformat() if deadline else None
            raw_task["deadline_time"] = (
                deadline_time.strftime("%H:%M") if deadline and deadline_time else None
            )
            raw_task["deadline_notified_at"] = None
            if deadline is None:
                raw_task["recurrence"] = None
                raw_task["recurrence_anchor_day"] = None
            elif normalize_recurrence(raw_task.get("recurrence")):
                raw_task["recurrence_anchor_day"] = get_recurrence_anchor_day(
                    normalize_recurrence(raw_task.get("recurrence")),
                    deadline,
                )
            self._write_raw_tasks(tasks)
            return True

        return False

    def update_task_recurrence_by_family(
        self,
        family_id: str,
        task_id: int,
        recurrence: Optional[str],
    ) -> Optional[Task]:
        """Update recurrence for a task belonging to a specific family."""
        tasks = self._read_raw_tasks()

        for raw_task in tasks:
            task = _task_from_dict(raw_task)
            if task is None or task.family_id != family_id or task.id != task_id:
                continue

            normalized_recurrence = (
                normalize_recurrence(recurrence) if task.deadline is not None else None
            )
            raw_task["recurrence"] = normalized_recurrence
            raw_task["recurrence_anchor_day"] = get_recurrence_anchor_day(
                normalized_recurrence,
                task.deadline,
            )
            self._write_raw_tasks(tasks)
            return _task_from_dict(raw_task)

        return None

    def update_task_snooze_by_family(
        self,
        family_id: str,
        task_id: int,
        snoozed_until: Optional[datetime],
    ) -> Optional[Task]:
        """Update snooze date for a task belonging to a specific family."""
        tasks = self._read_raw_tasks()

        for raw_task in tasks:
            task = _task_from_dict(raw_task)
            if task is None or task.family_id != family_id or task.id != task_id:
                continue

            raw_task["snoozed_until"] = (
                snoozed_until.isoformat() if snoozed_until else None
            )
            self._write_raw_tasks(tasks)
            return _task_from_dict(raw_task)

        return None

    def delete_task_by_family(self, family_id: str, task_id: int) -> Optional[Task]:
        """Delete a task belonging to a specific family."""
        tasks = self._read_raw_tasks()
        remaining: List[Dict[str, Any]] = []
        deleted_task: Optional[Task] = None

        for raw_task in tasks:
            task = _task_from_dict(raw_task)
            if task is not None and task.family_id == family_id and task.id == task_id:
                deleted_task = task
                continue
            remaining.append(raw_task)

        if deleted_task is not None:
            self._write_raw_tasks(remaining)
        return deleted_task

    def complete_task_by_family(
        self,
        family_id: str,
        task_id: int,
        completed_at: Optional[datetime] = None,
    ) -> Optional[Task]:
        """Mark a task as completed without deleting it from history."""
        tasks = self._read_raw_tasks()
        for raw_task in tasks:
            task = _task_from_dict(raw_task)
            if task is None or task.family_id != family_id or task.id != task_id:
                continue
            if task.completed_at is not None:
                return task
            raw_task["completed_at"] = (completed_at or datetime.now(timezone.utc)).isoformat()
            raw_task["deadline_notified_at"] = None
            self._write_raw_tasks(tasks)
            return _task_from_dict(raw_task)
        return None

    def complete_task_once_by_family(
        self,
        family_id: str,
        task_id: int,
        completed_at: Optional[datetime] = None,
    ) -> tuple[Optional[Task], bool]:
        """Complete once and report whether this call changed the task."""
        lock = _get_file_lock(self.file_path)
        with lock:
            tasks = self._read_raw_tasks()
            for raw_task in tasks:
                task = _task_from_dict(raw_task)
                if task is None or task.family_id != family_id or task.id != task_id:
                    continue
                if task.completed_at is not None:
                    return task, False
                raw_task["completed_at"] = (completed_at or datetime.now(timezone.utc)).isoformat()
                raw_task["deadline_notified_at"] = None
                self._write_raw_tasks_unlocked(tasks)
                return _task_from_dict(raw_task), True
        return None, False

    def delete_tasks_by_family(self, family_id: str) -> int:
        """Delete every task belonging to a specific family."""
        tasks = self._read_raw_tasks()
        remaining: List[Dict[str, Any]] = []
        deleted_count = 0

        for raw_task in tasks:
            task = _task_from_dict(raw_task)
            if task is not None and task.family_id == family_id:
                deleted_count += 1
                continue
            remaining.append(raw_task)

        if deleted_count:
            self._write_raw_tasks(remaining)
        return deleted_count

    def delete_task_by_chat(self, chat_id: int, task_id: int) -> bool:
        """Delete a task belonging to a specific chat."""
        tasks = self._read_raw_tasks()
        remaining: List[Dict[str, Any]] = []
        deleted = False

        for raw_task in tasks:
            task = _task_from_dict(raw_task)
            if task is not None and task.chat_id == chat_id and task.id == task_id:
                deleted = True
                continue
            remaining.append(raw_task)

        if deleted:
            self._write_raw_tasks(remaining)
        return deleted

    def _read_raw_tasks(self) -> List[Dict[str, Any]]:
        if not self.file_path.exists():
            return []
        with self.file_path.open("r", encoding="utf-8") as source:
            loaded = json.load(source)
        if not isinstance(loaded, list):
            return []
        return [item for item in loaded if isinstance(item, dict)]

    def _write_raw_tasks(self, tasks: List[Dict[str, Any]]) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        lock = _get_file_lock(self.file_path)
        with lock:
            self._write_raw_tasks_unlocked(tasks)

    def _write_raw_tasks_unlocked(self, tasks: List[Dict[str, Any]]) -> None:
        temp_path = self.file_path.with_suffix(f"{self.file_path.suffix}.tmp")
        with temp_path.open("w", encoding="utf-8") as destination:
            json.dump(tasks, destination, ensure_ascii=False, indent=2)
        os.replace(temp_path, self.file_path)


def default_tasks_file_path() -> Path:
    """Return default path for persisted tasks."""
    return Path(__file__).resolve().parents[2] / "data" / "tasks.json"


def _task_from_dict(raw: Dict[str, Any]) -> Optional[Task]:
    try:
        task_id = int(raw["id"])
        raw_chat_id = raw.get("created_by_chat_id", raw.get("chat_id"))
        chat_id = int(raw_chat_id)
        family_id = str(raw.get("family_id") or DEFAULT_FAMILY_ID)
        list_id = str(raw.get("list_id") or DEFAULT_TASK_LIST_ID)
        text = str(raw["text"])
        created_at = datetime.fromisoformat(str(raw["created_at"]))
        raw_deadline = raw.get("deadline")
        deadline = date.fromisoformat(str(raw_deadline)) if raw_deadline else None
        raw_deadline_time = raw.get("deadline_time")
        deadline_time = (
            time.fromisoformat(str(raw_deadline_time)) if raw_deadline_time else None
        )
        raw_deadline_notified_at = raw.get("deadline_notified_at")
        deadline_notified_at = (
            datetime.fromisoformat(str(raw_deadline_notified_at))
            if raw_deadline_notified_at
            else None
        )
        raw_snoozed_until = raw.get("snoozed_until")
        snoozed_until = (
            datetime.fromisoformat(str(raw_snoozed_until))
            if raw_snoozed_until
            else None
        )
        note = str(raw["note"]) if raw.get("note") is not None else None
        reminder_enabled = bool(raw.get("reminder_enabled", True))
        raw_completed_at = raw.get("completed_at")
        completed_at = (
            datetime.fromisoformat(str(raw_completed_at))
            if raw_completed_at
            else None
        )
        recurrence = normalize_recurrence(raw.get("recurrence"))
        raw_recurrence_anchor_day = raw.get("recurrence_anchor_day")
        recurrence_anchor_day = (
            int(raw_recurrence_anchor_day) if raw_recurrence_anchor_day else None
        )
    except (KeyError, TypeError, ValueError):
        return None

    if deadline is None:
        recurrence = None
        recurrence_anchor_day = None
    else:
        recurrence_anchor_day = get_recurrence_anchor_day(
            recurrence,
            deadline,
            anchor_day=recurrence_anchor_day,
        )

    return Task(
        id=task_id,
        family_id=family_id,
        list_id=list_id,
        chat_id=chat_id,
        text=text,
        deadline=deadline,
        deadline_time=deadline_time if deadline is not None else None,
        created_at=created_at,
        deadline_notified_at=deadline_notified_at,
        recurrence=recurrence,
        recurrence_anchor_day=recurrence_anchor_day,
        snoozed_until=snoozed_until,
        note=note,
        reminder_enabled=reminder_enabled,
        completed_at=completed_at,
    )


def _get_file_lock(file_path: Path) -> threading.Lock:
    resolved = file_path.resolve()
    with _FILE_LOCKS_GUARD:
        lock = _FILE_LOCKS.get(resolved)
        if lock is None:
            lock = threading.Lock()
            _FILE_LOCKS[resolved] = lock
        return lock


def _is_active_task(task: Task, now: Optional[datetime] = None) -> bool:
    return task.completed_at is None and not _is_task_snoozed(task, now)


def _is_visible_to_mini(task: Task, now: Optional[datetime], include_completed: bool) -> bool:
    if task.completed_at is not None:
        return include_completed
    return not _is_task_snoozed(task, now)


def _task_sort_key(task: Task) -> tuple[int, date, int, time, int]:
    if task.deadline is None:
        return (1, date.max, 1, time.max, task.id)
    if task.deadline_time is None:
        return (0, task.deadline, 1, time.max, task.id)
    return (0, task.deadline, 0, task.deadline_time, task.id)


def _snoozed_task_sort_key(task: Task) -> tuple[datetime, int]:
    return (task.snoozed_until or datetime.max.replace(tzinfo=timezone.utc), task.id)


def _is_task_snoozed(task: Task, now: Optional[datetime] = None) -> bool:
    if task.snoozed_until is None:
        return False
    reference_now = now or datetime.now(tz=task.snoozed_until.tzinfo or timezone.utc)
    snoozed_until = task.snoozed_until
    if snoozed_until.tzinfo is None and reference_now.tzinfo is not None:
        reference_now = reference_now.replace(tzinfo=None)
    if snoozed_until.tzinfo is not None and reference_now.tzinfo is None:
        reference_now = reference_now.replace(tzinfo=snoozed_until.tzinfo)
    return snoozed_until > reference_now
