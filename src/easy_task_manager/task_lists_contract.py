"""Contracts for family task-list flow."""

from __future__ import annotations

from typing import Sequence

from easy_task_manager.task_list_storage import TaskList

TASK_LISTS_ADD_CALLBACK_DATA = "todo:lists:add"
TASK_LIST_OPEN_CALLBACK_PREFIX = "todo:list:open:"
TASK_LIST_CREATE_CALLBACK_PREFIX = "todo:lists:create:"
ADD_TASK_TO_LIST_CALLBACK_PREFIX = "todo:add:list:"

TASK_LISTS_TEXT = "Выбери список дел."
TASK_LISTS_EMPTY_PRESETS_TEXT = "Все готовые списки уже добавлены."
TASK_LISTS_ADD_TEXT = "Какой список добавить?"
TASK_LIST_CREATED_TEMPLATE = "Добавил список: {title}"
ASK_TASK_LIST_TEXT = "В какой список добавить дело?"
CHANGE_TASK_LIST_TEXT = "В какой список перенести дело?"
CHANGE_TASK_LIST_EMPTY_TEXT = "Других списков пока нет."
TASK_LIST_CHANGED_TEMPLATE = "Перенес задачу в список: {title}"
TASK_LIST_BACK_BUTTON_TEXT = "Назад"
TASK_LIST_ADD_BUTTON_TEXT = "Добавить список"


def build_task_list_open_callback(list_id: str) -> str:
    return f"{TASK_LIST_OPEN_CALLBACK_PREFIX}{list_id}"


def build_task_list_create_callback(preset_id: str) -> str:
    return f"{TASK_LIST_CREATE_CALLBACK_PREFIX}{preset_id}"


def build_add_task_to_list_callback(list_id: str) -> str:
    return f"{ADD_TASK_TO_LIST_CALLBACK_PREFIX}{list_id}"


def parse_callback_suffix(callback_data: str | None, prefix: str) -> str | None:
    if callback_data is None or not callback_data.startswith(prefix):
        return None
    value = callback_data.removeprefix(prefix).strip()
    return value or None


def build_task_lists_text(task_lists: Sequence[TaskList], task_counts: dict[str, int]) -> str:
    if not task_lists:
        return TASK_LISTS_TEXT
    lines = [TASK_LISTS_TEXT]
    for task_list in task_lists:
        count = task_counts.get(task_list.id, 0)
        lines.append(f"{task_list.title}: {count}")
    return "\n".join(lines)
