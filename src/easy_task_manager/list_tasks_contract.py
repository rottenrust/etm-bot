"""Contracts for list-tasks flow."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import groupby
from typing import Mapping, Optional, Sequence

from easy_task_manager.deadline_utils import DATE_FORMAT, format_snooze_until_for_user
from easy_task_manager.recurrence import get_recurrence_label
from easy_task_manager.task_storage import DEFAULT_TASK_LIST_ID, Task

LIST_EMPTY_TEXT = "Список пока пуст."
LIST_HINTS_TEXT = "Выбери задачу на этой странице."
TASKS_PER_PAGE = 6
TASK_DONE_TEXT = "Ты молодец!"
TASK_WITHOUT_DEADLINE_TEXT = "Без дедлайна"
SNOOZED_LIST_EMPTY_TEXT = "Отложенных задач в этом списке нет."
TASK_HINT_CALLBACK_PREFIX = "todo:list:hint:"
TASK_SNOOZED_HINT_CALLBACK_PREFIX = "todo:list:snoozed:hint:"
TASK_DONE_CALLBACK_PREFIX = "todo:list:done:"
TASK_DEADLINE_MENU_CALLBACK_PREFIX = "todo:list:deadline:menu:"
TASK_DEADLINE_TODAY_CALLBACK_PREFIX = "todo:list:deadline:today:"
TASK_DEADLINE_TOMORROW_CALLBACK_PREFIX = "todo:list:deadline:tomorrow:"
TASK_DEADLINE_CUSTOM_CALLBACK_PREFIX = "todo:list:deadline:custom:"
TASK_DEADLINE_REMOVE_CALLBACK_PREFIX = "todo:list:deadline:remove:"
TASK_RECURRENCE_MENU_CALLBACK_PREFIX = "todo:list:recurrence:menu:"
TASK_RECURRENCE_DAILY_CALLBACK_PREFIX = "todo:list:recurrence:daily:"
TASK_RECURRENCE_WEEKLY_CALLBACK_PREFIX = "todo:list:recurrence:weekly:"
TASK_RECURRENCE_MONTHLY_CALLBACK_PREFIX = "todo:list:recurrence:monthly:"
TASK_RECURRENCE_REMOVE_CALLBACK_PREFIX = "todo:list:recurrence:remove:"
TASK_SNOOZE_MENU_CALLBACK_PREFIX = "todo:list:snooze:menu:"
TASK_SNOOZE_EVENING_CALLBACK_PREFIX = "todo:list:snooze:evening:"
TASK_SNOOZE_TOMORROW_CALLBACK_PREFIX = "todo:list:snooze:tomorrow:"
TASK_SNOOZE_WEEKEND_CALLBACK_PREFIX = "todo:list:snooze:weekend:"
TASK_SNOOZE_NEXT_WEEK_CALLBACK_PREFIX = "todo:list:snooze:next-week:"
TASK_SNOOZE_CUSTOM_CALLBACK_PREFIX = "todo:list:snooze:custom:"
TASK_SNOOZE_REMOVE_CALLBACK_PREFIX = "todo:list:snooze:remove:"
TASK_BACK_CALLBACK_DATA = "todo:list:back"
TASK_BACK_CALLBACK_PREFIX = "todo:list:back:"
TASK_SNOOZED_BACK_CALLBACK_PREFIX = "todo:list:snoozed:back:"
TASK_PAGE_CALLBACK_PREFIX = "todo:list:page:"
TASK_SNOOZED_PAGE_CALLBACK_PREFIX = "todo:list:snoozed:page:"
TASK_PAGE_NOOP_CALLBACK_DATA = "todo:list:page:noop"
TASK_CHANGE_LIST_CALLBACK_PREFIX = "todo:list:change-list:"
TASK_MOVE_TO_LIST_CALLBACK_PREFIX = "todo:list:move-list:"
TASK_SNOOZED_OPEN_CALLBACK_PREFIX = "todo:list:snoozed:open:"
TASK_DONE_BUTTON_TEXT = "Сделал"
TASK_SNOOZE_BUTTON_TEXT = "Отложить"
TASK_DEADLINE_BUTTON_TEXT = "Дедлайн"
TASK_CHANGE_LIST_BUTTON_TEXT = "Изменить список"
TASK_RECURRENCE_BUTTON_TEXT = "Повторять"
TASK_SNOOZE_EVENING_BUTTON_TEXT = "Сегодня вечером"
TASK_SNOOZE_TOMORROW_BUTTON_TEXT = "Завтра"
TASK_SNOOZE_WEEKEND_BUTTON_TEXT = "В выходные"
TASK_SNOOZE_NEXT_WEEK_BUTTON_TEXT = "Через неделю"
TASK_SNOOZE_CUSTOM_BUTTON_TEXT = "Свой срок"
TASK_SNOOZE_REMOVE_BUTTON_TEXT = "Убрать отложение"
TASK_DEADLINE_TODAY_BUTTON_TEXT = "Сегодня"
TASK_DEADLINE_TOMORROW_BUTTON_TEXT = "Завтра"
TASK_DEADLINE_CUSTOM_BUTTON_TEXT = "Свой дедлайн"
TASK_DEADLINE_REMOVE_BUTTON_TEXT = "Удалить дедлайн"
TASK_RECURRENCE_DAILY_BUTTON_TEXT = "Каждый день"
TASK_RECURRENCE_WEEKLY_BUTTON_TEXT = "Каждую неделю"
TASK_RECURRENCE_MONTHLY_BUTTON_TEXT = "Каждый месяц"
TASK_RECURRENCE_REMOVE_BUTTON_TEXT = "Не повторять"
TASK_RECURRENCE_UPDATED_TEMPLATE = "Теперь задача повторяется: {recurrence_label}"
TASK_RECURRENCE_REMOVED_TEXT = "Повторение удалил."
TASK_RECURRENCE_NEEDS_DEADLINE_TEXT = "Сначала добавь дедлайн, чтобы включить повтор."
TASK_RECURRING_NEXT_TEMPLATE = "Следующий раз: {deadline}"
TASK_SNOOZE_CUSTOM_PROMPT_TEXT = "На какую дату отложить? Напиши в формате дд.мм.гггг."
TASK_SNOOZE_CUSTOM_INVALID_TEXT = "Не понял дату. Напиши в формате дд.мм.гггг."
TASK_SNOOZE_UPDATED_TEMPLATE = "Отложил до {snoozed_until}"
TASK_SNOOZE_REMOVED_TEXT = "Отложение убрал."
TASK_BACK_BUTTON_TEXT = "Назад"
TASK_NEXT_PAGE_BUTTON_TEXT = "→"
TASK_PREVIOUS_PAGE_BUTTON_TEXT = "←"


@dataclass(frozen=True)
class TaskPage:
    tasks: Sequence[Task]
    page: int
    total_pages: int


def format_task_line(task: Task, list_title: str | None = None) -> str:
    list_part = ""
    if task.list_id != DEFAULT_TASK_LIST_ID and list_title:
        list_part = f" [{list_title}]"
    time_part = f" {task.deadline_time.strftime('%H:%M')}" if task.deadline_time else ""
    recurrence_label = get_recurrence_label(task.recurrence)
    recurrence_part = f" ({recurrence_label})" if recurrence_label else ""
    return f"#{task.id}{list_part} {task.text}{time_part}{recurrence_part}"


def build_task_list_text(
    tasks: Sequence[Task],
    list_titles: Mapping[str, str] | None = None,
) -> str:
    if not tasks:
        return LIST_EMPTY_TEXT
    titles = list_titles or {}
    blocks: list[str] = []
    sorted_tasks = sorted(tasks, key=_task_display_sort_key)
    for deadline, deadline_tasks_iter in groupby(sorted_tasks, key=lambda task: task.deadline):
        deadline_tasks = list(deadline_tasks_iter)
        if deadline is None:
            header = TASK_WITHOUT_DEADLINE_TEXT
        else:
            header = deadline.strftime(DATE_FORMAT)
        lines = [header]
        lines.extend(format_task_line(task, titles.get(task.list_id)) for task in deadline_tasks)
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def build_snoozed_task_list_text(tasks: Sequence[Task]) -> str:
    if not tasks:
        return SNOOZED_LIST_EMPTY_TEXT
    lines: list[str] = []
    for task in sorted(tasks, key=lambda item: (item.snoozed_until, item.id)):
        if task.snoozed_until is None:
            continue
        lines.append(
            f"Отложено до {format_snooze_until_for_user(task.snoozed_until)}\n"
            f"{format_task_line(task)}"
        )
    return "\n\n".join(lines) if lines else SNOOZED_LIST_EMPTY_TEXT


def build_task_page(tasks: Sequence[Task], page: int) -> TaskPage:
    total_pages = max(1, (len(tasks) + TASKS_PER_PAGE - 1) // TASKS_PER_PAGE)
    safe_page = min(max(page, 0), total_pages - 1)
    start_index = safe_page * TASKS_PER_PAGE
    end_index = start_index + TASKS_PER_PAGE
    return TaskPage(
        tasks=tasks[start_index:end_index],
        page=safe_page,
        total_pages=total_pages,
    )


def build_task_page_hint_text(page: int, total_pages: int) -> str:
    if total_pages <= 1:
        return LIST_HINTS_TEXT
    return f"{LIST_HINTS_TEXT}\nСтраница {page + 1} из {total_pages}"


def build_task_hint_callback(
    task_id: int,
    list_id: Optional[str] = None,
    page: int = 0,
) -> str:
    if list_id is not None and page > 0:
        return f"{TASK_HINT_CALLBACK_PREFIX}{task_id}:{page}:{list_id}"
    return f"{TASK_HINT_CALLBACK_PREFIX}{task_id}"


def build_task_snoozed_hint_callback(task_id: int, list_id: str, page: int = 0) -> str:
    return f"{TASK_SNOOZED_HINT_CALLBACK_PREFIX}{task_id}:{page}:{list_id}"


def build_task_done_callback(
    task_id: int,
    list_id: Optional[str] = None,
    page: int = 0,
) -> str:
    if list_id is not None and page > 0:
        return f"{TASK_DONE_CALLBACK_PREFIX}{task_id}:{page}:{list_id}"
    return f"{TASK_DONE_CALLBACK_PREFIX}{task_id}"


def build_task_deadline_menu_callback(
    task_id: int,
    list_id: Optional[str] = None,
    page: int = 0,
) -> str:
    if list_id is not None and page > 0:
        return f"{TASK_DEADLINE_MENU_CALLBACK_PREFIX}{task_id}:{page}:{list_id}"
    return f"{TASK_DEADLINE_MENU_CALLBACK_PREFIX}{task_id}"


def build_task_snooze_menu_callback(
    task_id: int,
    list_id: Optional[str] = None,
    page: int = 0,
) -> str:
    if list_id is not None:
        return f"{TASK_SNOOZE_MENU_CALLBACK_PREFIX}{task_id}:{page}:{list_id}"
    return f"{TASK_SNOOZE_MENU_CALLBACK_PREFIX}{task_id}"


def build_task_snooze_evening_callback(
    task_id: int,
    list_id: Optional[str] = None,
    page: int = 0,
) -> str:
    if list_id is not None:
        return f"{TASK_SNOOZE_EVENING_CALLBACK_PREFIX}{task_id}:{page}:{list_id}"
    return f"{TASK_SNOOZE_EVENING_CALLBACK_PREFIX}{task_id}"


def build_task_snooze_tomorrow_callback(
    task_id: int,
    list_id: Optional[str] = None,
    page: int = 0,
) -> str:
    if list_id is not None:
        return f"{TASK_SNOOZE_TOMORROW_CALLBACK_PREFIX}{task_id}:{page}:{list_id}"
    return f"{TASK_SNOOZE_TOMORROW_CALLBACK_PREFIX}{task_id}"


def build_task_snooze_weekend_callback(
    task_id: int,
    list_id: Optional[str] = None,
    page: int = 0,
) -> str:
    if list_id is not None:
        return f"{TASK_SNOOZE_WEEKEND_CALLBACK_PREFIX}{task_id}:{page}:{list_id}"
    return f"{TASK_SNOOZE_WEEKEND_CALLBACK_PREFIX}{task_id}"


def build_task_snooze_next_week_callback(
    task_id: int,
    list_id: Optional[str] = None,
    page: int = 0,
) -> str:
    if list_id is not None:
        return f"{TASK_SNOOZE_NEXT_WEEK_CALLBACK_PREFIX}{task_id}:{page}:{list_id}"
    return f"{TASK_SNOOZE_NEXT_WEEK_CALLBACK_PREFIX}{task_id}"


def build_task_snooze_custom_callback(
    task_id: int,
    list_id: Optional[str] = None,
    page: int = 0,
) -> str:
    if list_id is not None:
        return f"{TASK_SNOOZE_CUSTOM_CALLBACK_PREFIX}{task_id}:{page}:{list_id}"
    return f"{TASK_SNOOZE_CUSTOM_CALLBACK_PREFIX}{task_id}"


def build_task_snooze_remove_callback(
    task_id: int,
    list_id: Optional[str] = None,
    page: int = 0,
) -> str:
    if list_id is not None:
        return f"{TASK_SNOOZE_REMOVE_CALLBACK_PREFIX}{task_id}:{page}:{list_id}"
    return f"{TASK_SNOOZE_REMOVE_CALLBACK_PREFIX}{task_id}"


def build_task_deadline_today_callback(
    task_id: int,
    list_id: Optional[str] = None,
    page: int = 0,
) -> str:
    if list_id is not None and page > 0:
        return f"{TASK_DEADLINE_TODAY_CALLBACK_PREFIX}{task_id}:{page}:{list_id}"
    return f"{TASK_DEADLINE_TODAY_CALLBACK_PREFIX}{task_id}"


def build_task_deadline_tomorrow_callback(
    task_id: int,
    list_id: Optional[str] = None,
    page: int = 0,
) -> str:
    if list_id is not None and page > 0:
        return f"{TASK_DEADLINE_TOMORROW_CALLBACK_PREFIX}{task_id}:{page}:{list_id}"
    return f"{TASK_DEADLINE_TOMORROW_CALLBACK_PREFIX}{task_id}"


def build_task_deadline_custom_callback(
    task_id: int,
    list_id: Optional[str] = None,
    page: int = 0,
) -> str:
    if list_id is not None and page > 0:
        return f"{TASK_DEADLINE_CUSTOM_CALLBACK_PREFIX}{task_id}:{page}:{list_id}"
    return f"{TASK_DEADLINE_CUSTOM_CALLBACK_PREFIX}{task_id}"


def build_task_deadline_remove_callback(
    task_id: int,
    list_id: Optional[str] = None,
    page: int = 0,
) -> str:
    if list_id is not None and page > 0:
        return f"{TASK_DEADLINE_REMOVE_CALLBACK_PREFIX}{task_id}:{page}:{list_id}"
    return f"{TASK_DEADLINE_REMOVE_CALLBACK_PREFIX}{task_id}"


def build_task_recurrence_menu_callback(
    task_id: int,
    list_id: Optional[str] = None,
    page: int = 0,
) -> str:
    if list_id is not None and page > 0:
        return f"{TASK_RECURRENCE_MENU_CALLBACK_PREFIX}{task_id}:{page}:{list_id}"
    return f"{TASK_RECURRENCE_MENU_CALLBACK_PREFIX}{task_id}"


def build_task_recurrence_daily_callback(
    task_id: int,
    list_id: Optional[str] = None,
    page: int = 0,
) -> str:
    if list_id is not None and page > 0:
        return f"{TASK_RECURRENCE_DAILY_CALLBACK_PREFIX}{task_id}:{page}:{list_id}"
    return f"{TASK_RECURRENCE_DAILY_CALLBACK_PREFIX}{task_id}"


def build_task_recurrence_weekly_callback(
    task_id: int,
    list_id: Optional[str] = None,
    page: int = 0,
) -> str:
    if list_id is not None and page > 0:
        return f"{TASK_RECURRENCE_WEEKLY_CALLBACK_PREFIX}{task_id}:{page}:{list_id}"
    return f"{TASK_RECURRENCE_WEEKLY_CALLBACK_PREFIX}{task_id}"


def build_task_recurrence_monthly_callback(
    task_id: int,
    list_id: Optional[str] = None,
    page: int = 0,
) -> str:
    if list_id is not None and page > 0:
        return f"{TASK_RECURRENCE_MONTHLY_CALLBACK_PREFIX}{task_id}:{page}:{list_id}"
    return f"{TASK_RECURRENCE_MONTHLY_CALLBACK_PREFIX}{task_id}"


def build_task_recurrence_remove_callback(
    task_id: int,
    list_id: Optional[str] = None,
    page: int = 0,
) -> str:
    if list_id is not None and page > 0:
        return f"{TASK_RECURRENCE_REMOVE_CALLBACK_PREFIX}{task_id}:{page}:{list_id}"
    return f"{TASK_RECURRENCE_REMOVE_CALLBACK_PREFIX}{task_id}"


def build_task_change_list_callback(task_id: int, list_id: str, page: int = 0) -> str:
    return f"{TASK_CHANGE_LIST_CALLBACK_PREFIX}{task_id}:{page}:{list_id}"


def build_task_move_to_list_callback(
    task_id: int,
    target_list_id: str,
    source_list_id: str,
    page: int = 0,
) -> str:
    return f"{TASK_MOVE_TO_LIST_CALLBACK_PREFIX}{task_id}:{page}:{source_list_id}:{target_list_id}"


def build_task_page_callback(list_id: str, page: int) -> str:
    return f"{TASK_PAGE_CALLBACK_PREFIX}{page}:{list_id}"


def build_task_snoozed_open_callback(list_id: str) -> str:
    return f"{TASK_SNOOZED_OPEN_CALLBACK_PREFIX}{list_id}"


def build_task_snoozed_page_callback(list_id: str, page: int) -> str:
    return f"{TASK_SNOOZED_PAGE_CALLBACK_PREFIX}{page}:{list_id}"


def build_task_back_callback(list_id: str, page: int = 0) -> str:
    if page > 0:
        return f"{TASK_BACK_CALLBACK_PREFIX}{page}:{list_id}"
    return f"{TASK_BACK_CALLBACK_PREFIX}{list_id}"


def build_task_snoozed_back_callback(list_id: str, page: int = 0) -> str:
    return f"{TASK_SNOOZED_BACK_CALLBACK_PREFIX}{page}:{list_id}"


def parse_task_hint_context(
    callback_data: Optional[str],
) -> tuple[Optional[int], Optional[int], Optional[str]]:
    return parse_task_action_context(callback_data, TASK_HINT_CALLBACK_PREFIX)


def parse_task_snoozed_hint_context(
    callback_data: Optional[str],
) -> tuple[Optional[int], Optional[int], Optional[str]]:
    return parse_task_action_context(callback_data, TASK_SNOOZED_HINT_CALLBACK_PREFIX)


def parse_task_action_context(
    callback_data: Optional[str],
    prefix: str,
) -> tuple[Optional[int], Optional[int], Optional[str]]:
    if callback_data is None or not callback_data.startswith(prefix):
        return None, None, None

    raw_value = callback_data.removeprefix(prefix)
    parts = raw_value.split(":", 2)
    try:
        task_id = int(parts[0])
    except (IndexError, ValueError):
        return None, None, None

    if len(parts) < 3:
        return task_id, 0, None

    try:
        page = int(parts[1])
    except ValueError:
        return task_id, 0, None
    list_id = parts[2].strip() or None
    return task_id, max(page, 0), list_id


def parse_task_page_callback(
    callback_data: Optional[str],
) -> tuple[Optional[int], Optional[str]]:
    if callback_data is None or not callback_data.startswith(TASK_PAGE_CALLBACK_PREFIX):
        return None, None
    raw_value = callback_data.removeprefix(TASK_PAGE_CALLBACK_PREFIX)
    parts = raw_value.split(":", 1)
    try:
        page = int(parts[0])
    except (IndexError, ValueError):
        return None, None
    list_id = parts[1].strip() if len(parts) == 2 else ""
    return max(page, 0), list_id or None


def parse_task_snoozed_page_callback(
    callback_data: Optional[str],
) -> tuple[Optional[int], Optional[str]]:
    if callback_data is None or not callback_data.startswith(TASK_SNOOZED_PAGE_CALLBACK_PREFIX):
        return None, None
    raw_value = callback_data.removeprefix(TASK_SNOOZED_PAGE_CALLBACK_PREFIX)
    parts = raw_value.split(":", 1)
    try:
        page = int(parts[0])
    except (IndexError, ValueError):
        return None, None
    list_id = parts[1].strip() if len(parts) == 2 else ""
    return max(page, 0), list_id or None


def parse_task_move_to_list_callback(
    callback_data: Optional[str],
) -> tuple[Optional[int], int, Optional[str], Optional[str]]:
    if callback_data is None or not callback_data.startswith(TASK_MOVE_TO_LIST_CALLBACK_PREFIX):
        return None, 0, None, None
    raw_value = callback_data.removeprefix(TASK_MOVE_TO_LIST_CALLBACK_PREFIX)
    parts = raw_value.split(":", 3)
    try:
        task_id = int(parts[0])
        page = max(int(parts[1]), 0)
    except (IndexError, ValueError):
        return None, 0, None, None
    source_list_id = parts[2].strip() if len(parts) >= 3 else ""
    target_list_id = parts[3].strip() if len(parts) >= 4 else ""
    return task_id, page, source_list_id or None, target_list_id or None


def parse_task_back_context(
    callback_data: Optional[str],
) -> tuple[Optional[str], int]:
    if callback_data is None or not callback_data.startswith(TASK_BACK_CALLBACK_PREFIX):
        return None, 0

    raw_value = callback_data.removeprefix(TASK_BACK_CALLBACK_PREFIX)
    parts = raw_value.split(":", 1)
    if len(parts) == 2:
        try:
            return parts[1].strip() or None, max(int(parts[0]), 0)
        except ValueError:
            pass
    return raw_value.strip() or None, 0


def parse_task_snoozed_back_context(
    callback_data: Optional[str],
) -> tuple[Optional[str], int]:
    if callback_data is None or not callback_data.startswith(TASK_SNOOZED_BACK_CALLBACK_PREFIX):
        return None, 0
    raw_value = callback_data.removeprefix(TASK_SNOOZED_BACK_CALLBACK_PREFIX)
    parts = raw_value.split(":", 1)
    try:
        page = int(parts[0])
    except (IndexError, ValueError):
        return None, 0
    list_id = parts[1].strip() if len(parts) == 2 else ""
    return list_id or None, max(page, 0)


def _task_display_sort_key(task: Task) -> tuple[int, object, int, object, int]:
    if task.deadline is None:
        return (1, "", 1, "", task.id)
    if task.deadline_time is None:
        return (0, task.deadline, 1, "", task.id)
    return (0, task.deadline, 0, task.deadline_time, task.id)
