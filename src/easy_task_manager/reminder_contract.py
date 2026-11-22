"""Contracts for due-task reminders."""

from __future__ import annotations

from typing import Mapping, Sequence

from easy_task_manager.list_tasks_contract import build_task_list_text
from easy_task_manager.task_storage import Task

MORNING_REMINDER_HEADER = "Сегодня тебе надо сделать вот это:"
EVENING_REMINDER_HEADER = "Тебе все ещё сегодня надо сделать это:"
EXACT_DEADLINE_SINGLE_HEADER = "Наступил дедлайн по задаче:"
EXACT_DEADLINE_MULTIPLE_HEADER = "Наступил дедлайн по задачам:"


def build_morning_reminder_text(
    tasks: Sequence[Task],
    list_titles: Mapping[str, str] | None = None,
) -> str:
    """Build morning reminder text for due tasks."""
    return _build_reminder_text(
        header=MORNING_REMINDER_HEADER,
        tasks=tasks,
        list_titles=list_titles,
    )


def build_evening_reminder_text(
    tasks: Sequence[Task],
    list_titles: Mapping[str, str] | None = None,
) -> str:
    """Build evening reminder text for due tasks."""
    return _build_reminder_text(
        header=EVENING_REMINDER_HEADER,
        tasks=tasks,
        list_titles=list_titles,
    )


def build_exact_deadline_reminder_text(
    tasks: Sequence[Task],
    list_titles: Mapping[str, str] | None = None,
) -> str:
    """Build exact deadline reminder text for timed due tasks."""
    header = (
        EXACT_DEADLINE_SINGLE_HEADER
        if len(tasks) == 1
        else EXACT_DEADLINE_MULTIPLE_HEADER
    )
    return _build_reminder_text(header=header, tasks=tasks, list_titles=list_titles)


def _build_reminder_text(
    header: str,
    tasks: Sequence[Task],
    list_titles: Mapping[str, str] | None = None,
) -> str:
    if not tasks:
        return ""
    return f"{header}\n{build_task_list_text(tasks, list_titles=list_titles)}"
