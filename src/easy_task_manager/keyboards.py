"""Inline keyboards used in the Telegram bot."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import WebAppInfo

from easy_task_manager.config import get_webapp_url
from easy_task_manager.add_task_contract import (
    DEADLINE_BUTTONS,
    DEADLINE_TIME_BUTTONS,
    RECURRENCE_BUTTONS,
)
from easy_task_manager.family_storage import FamilyMember
from easy_task_manager.list_tasks_contract import (
    TASK_BACK_BUTTON_TEXT,
    TASK_BACK_CALLBACK_DATA,
    TASK_CHANGE_LIST_BUTTON_TEXT,
    TASK_DEADLINE_BUTTON_TEXT,
    TASK_DEADLINE_CUSTOM_BUTTON_TEXT,
    TASK_DEADLINE_REMOVE_BUTTON_TEXT,
    TASK_DEADLINE_TODAY_BUTTON_TEXT,
    TASK_DEADLINE_TOMORROW_BUTTON_TEXT,
    TASK_DONE_BUTTON_TEXT,
    TASK_NEXT_PAGE_BUTTON_TEXT,
    TASK_PAGE_NOOP_CALLBACK_DATA,
    TASK_PREVIOUS_PAGE_BUTTON_TEXT,
    TASK_RECURRENCE_BUTTON_TEXT,
    TASK_RECURRENCE_DAILY_BUTTON_TEXT,
    TASK_RECURRENCE_MONTHLY_BUTTON_TEXT,
    TASK_RECURRENCE_REMOVE_BUTTON_TEXT,
    TASK_RECURRENCE_WEEKLY_BUTTON_TEXT,
    TASK_SNOOZE_BUTTON_TEXT,
    TASK_SNOOZE_CUSTOM_BUTTON_TEXT,
    TASK_SNOOZE_EVENING_BUTTON_TEXT,
    TASK_SNOOZE_NEXT_WEEK_BUTTON_TEXT,
    TASK_SNOOZE_REMOVE_BUTTON_TEXT,
    TASK_SNOOZE_TOMORROW_BUTTON_TEXT,
    TASK_SNOOZE_WEEKEND_BUTTON_TEXT,
    build_task_back_callback,
    build_task_change_list_callback,
    build_task_deadline_custom_callback,
    build_task_deadline_menu_callback,
    build_task_deadline_remove_callback,
    build_task_deadline_today_callback,
    build_task_deadline_tomorrow_callback,
    build_task_done_callback,
    build_task_hint_callback,
    build_task_move_to_list_callback,
    build_task_page_callback,
    build_task_recurrence_daily_callback,
    build_task_recurrence_menu_callback,
    build_task_recurrence_monthly_callback,
    build_task_recurrence_remove_callback,
    build_task_recurrence_weekly_callback,
    build_task_snooze_custom_callback,
    build_task_snooze_evening_callback,
    build_task_snooze_menu_callback,
    build_task_snooze_next_week_callback,
    build_task_snooze_remove_callback,
    build_task_snooze_tomorrow_callback,
    build_task_snooze_weekend_callback,
    build_task_snoozed_back_callback,
    build_task_snoozed_hint_callback,
    build_task_snoozed_open_callback,
    build_task_snoozed_page_callback,
)
from easy_task_manager.start_contract import (
    ADD_TASK_CALLBACK_DATA,
    BACK_TO_START_CALLBACK_DATA,
    CANCEL_REMOVE_FAMILY_MEMBER_CALLBACK_DATA,
    CONFIRM_REMOVE_FAMILY_MEMBER_CALLBACK_PREFIX,
    FAMILY_DELETE_CONFIRM_BUTTONS,
    FAMILY_MENU_CALLBACK_DATA,
    FAMILY_MENU_BUTTONS,
    NEW_USER_BUTTONS,
    REMOVE_FAMILY_MEMBER_CALLBACK_PREFIX,
    START_BUTTONS,
)
from easy_task_manager.task_list_storage import DEFAULT_TASK_LIST_ID, TaskList, TaskListPreset
from easy_task_manager.task_storage import Task
from easy_task_manager.task_lists_contract import (
    TASK_LIST_ADD_BUTTON_TEXT,
    TASK_LIST_BACK_BUTTON_TEXT,
    TASK_LISTS_ADD_CALLBACK_DATA,
    build_add_task_to_list_callback,
    build_task_list_create_callback,
    build_task_list_open_callback,
)


def build_start_keyboard() -> InlineKeyboardMarkup:
    """Build inline keyboard shown right after start."""
    rows = [
        [
            InlineKeyboardButton(
                text=START_BUTTONS[0].text,
                callback_data=START_BUTTONS[0].callback_data,
            ),
            InlineKeyboardButton(
                text=START_BUTTONS[1].text,
                callback_data=START_BUTTONS[1].callback_data,
            ),
        ],
        [
            InlineKeyboardButton(
                text=START_BUTTONS[2].text,
                callback_data=START_BUTTONS[2].callback_data,
            ),
        ],
    ]
    webapp_url = get_webapp_url()
    if webapp_url:
        rows.append(
            [
                InlineKeyboardButton(
                    text="Открыть мини-приложение",
                    web_app=WebAppInfo(url=webapp_url),
                )
            ]
        )
    return InlineKeyboardMarkup(
        inline_keyboard=rows
    )


def build_new_user_keyboard() -> InlineKeyboardMarkup:
    """Build inline keyboard for first public-bot onboarding choice."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=NEW_USER_BUTTONS[0].text,
                    callback_data=NEW_USER_BUTTONS[0].callback_data,
                ),
                InlineKeyboardButton(
                    text=NEW_USER_BUTTONS[1].text,
                    callback_data=NEW_USER_BUTTONS[1].callback_data,
                ),
            ]
        ]
    )


def build_family_menu_keyboard() -> InlineKeyboardMarkup:
    """Build inline keyboard for family-level actions."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=button.text, callback_data=button.callback_data)]
            for button in FAMILY_MENU_BUTTONS
        ]
    )


def build_family_members_keyboard(
    members: list[FamilyMember],
    actor_chat_id: int,
    owner_chat_id: int | None,
) -> InlineKeyboardMarkup:
    """Build keyboard for family member management."""
    rows: list[list[InlineKeyboardButton]] = []
    if actor_chat_id == owner_chat_id:
        for member in members:
            if member.chat_id == actor_chat_id:
                continue
            rows.append(
                [
                    InlineKeyboardButton(
                        text=f"Удалить {member.name}",
                        callback_data=f"{REMOVE_FAMILY_MEMBER_CALLBACK_PREFIX}{member.chat_id}",
                    )
                ]
            )

    rows.append(
        [
            InlineKeyboardButton(
                text=TASK_BACK_BUTTON_TEXT,
                callback_data=FAMILY_MENU_CALLBACK_DATA,
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_remove_family_member_confirm_keyboard(member_chat_id: int) -> InlineKeyboardMarkup:
    """Build keyboard for confirming member removal."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Да, удалить",
                    callback_data=f"{CONFIRM_REMOVE_FAMILY_MEMBER_CALLBACK_PREFIX}{member_chat_id}",
                ),
                InlineKeyboardButton(
                    text="Отмена",
                    callback_data=CANCEL_REMOVE_FAMILY_MEMBER_CALLBACK_DATA,
                ),
            ]
        ]
    )


def build_family_delete_confirm_keyboard() -> InlineKeyboardMarkup:
    """Build inline keyboard for destructive family deletion confirmation."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=FAMILY_DELETE_CONFIRM_BUTTONS[0].text,
                    callback_data=FAMILY_DELETE_CONFIRM_BUTTONS[0].callback_data,
                ),
                InlineKeyboardButton(
                    text=FAMILY_DELETE_CONFIRM_BUTTONS[1].text,
                    callback_data=FAMILY_DELETE_CONFIRM_BUTTONS[1].callback_data,
                ),
            ]
        ]
    )


def build_deadline_keyboard() -> InlineKeyboardMarkup:
    """Build inline keyboard for selecting deadline in add-task flow."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=DEADLINE_BUTTONS[0][0],
                    callback_data=DEADLINE_BUTTONS[0][1],
                ),
                InlineKeyboardButton(
                    text=DEADLINE_BUTTONS[1][0],
                    callback_data=DEADLINE_BUTTONS[1][1],
                ),
            ],
            [
                InlineKeyboardButton(
                    text=DEADLINE_BUTTONS[2][0],
                    callback_data=DEADLINE_BUTTONS[2][1],
                ),
                InlineKeyboardButton(
                    text=DEADLINE_BUTTONS[3][0],
                    callback_data=DEADLINE_BUTTONS[3][1],
                ),
            ],
        ]
    )


def build_deadline_time_keyboard() -> InlineKeyboardMarkup:
    """Build inline keyboard for skipping deadline time in add-task flow."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=DEADLINE_TIME_BUTTONS[0][0],
                    callback_data=DEADLINE_TIME_BUTTONS[0][1],
                )
            ]
        ]
    )


def build_recurrence_keyboard() -> InlineKeyboardMarkup:
    """Build inline keyboard for choosing recurrence in add-task flow."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=RECURRENCE_BUTTONS[0][0],
                    callback_data=RECURRENCE_BUTTONS[0][1],
                ),
                InlineKeyboardButton(
                    text=RECURRENCE_BUTTONS[1][0],
                    callback_data=RECURRENCE_BUTTONS[1][1],
                ),
            ],
            [
                InlineKeyboardButton(
                    text=RECURRENCE_BUTTONS[2][0],
                    callback_data=RECURRENCE_BUTTONS[2][1],
                ),
                InlineKeyboardButton(
                    text=RECURRENCE_BUTTONS[3][0],
                    callback_data=RECURRENCE_BUTTONS[3][1],
                ),
            ],
        ]
    )


def build_task_lists_keyboard(
    task_lists: list[TaskList],
    task_counts: dict[str, int],
) -> InlineKeyboardMarkup:
    """Build keyboard for choosing a family task list."""
    rows: list[list[InlineKeyboardButton]] = []
    for task_list in task_lists:
        count = task_counts.get(task_list.id, 0)
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{task_list.title} ({count})",
                    callback_data=build_task_list_open_callback(task_list.id),
                )
            ]
        )

    rows.append(
        [
            InlineKeyboardButton(
                text=TASK_LIST_ADD_BUTTON_TEXT,
                callback_data=TASK_LISTS_ADD_CALLBACK_DATA,
            )
        ]
    )
    rows.append(
        [
            InlineKeyboardButton(
                text=TASK_LIST_BACK_BUTTON_TEXT,
                callback_data=BACK_TO_START_CALLBACK_DATA,
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_task_list_presets_keyboard(presets: list[TaskListPreset]) -> InlineKeyboardMarkup:
    """Build keyboard with missing predefined task lists."""
    rows: list[list[InlineKeyboardButton]] = []
    for preset in presets:
        rows.append(
            [
                InlineKeyboardButton(
                    text=preset.title,
                    callback_data=build_task_list_create_callback(preset.id),
                )
            ]
        )

    rows.append(
        [
            InlineKeyboardButton(
                text=TASK_LIST_BACK_BUTTON_TEXT,
                callback_data=START_BUTTONS[1].callback_data,
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_add_task_list_choice_keyboard(task_lists: list[TaskList]) -> InlineKeyboardMarkup:
    """Build keyboard for choosing where a new task should be created."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=task_list.title,
                    callback_data=build_add_task_to_list_callback(task_list.id),
                )
            ]
            for task_list in task_lists
        ]
    )


def build_change_task_list_keyboard(
    task_id: int,
    source_list_id: str,
    page: int,
    task_lists: list[TaskList],
) -> InlineKeyboardMarkup:
    """Build keyboard for moving an existing task to another list."""
    rows = [
        [
            InlineKeyboardButton(
                text=task_list.title,
                callback_data=build_task_move_to_list_callback(
                    task_id=task_id,
                    target_list_id=task_list.id,
                    source_list_id=source_list_id,
                    page=page,
                ),
            )
        ]
        for task_list in task_lists
        if task_list.id != source_list_id
    ]
    rows.append(
        [
            InlineKeyboardButton(
                text=TASK_BACK_BUTTON_TEXT,
                callback_data=build_task_back_callback(source_list_id, page=page),
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_task_hints_keyboard(
    task_ids: list[int],
    buttons_per_row: int = 3,
    list_id: str | None = None,
    page: int = 0,
    total_pages: int = 1,
    snoozed_count: int = 0,
) -> InlineKeyboardMarkup:
    """Build inline keyboard with task number hints."""
    rows: list[list[InlineKeyboardButton]] = []
    current_row: list[InlineKeyboardButton] = []
    for task_id in task_ids:
        current_row.append(
            InlineKeyboardButton(
                text=f"#{task_id}",
                callback_data=build_task_hint_callback(
                    task_id=task_id,
                    list_id=list_id,
                    page=page,
                ),
            )
        )
        if len(current_row) == buttons_per_row:
            rows.append(current_row)
            current_row = []

    if current_row:
        rows.append(current_row)

    if total_pages > 1:
        pagination_row: list[InlineKeyboardButton] = []
        if page > 0 and list_id is not None:
            pagination_row.append(
                InlineKeyboardButton(
                    text=TASK_PREVIOUS_PAGE_BUTTON_TEXT,
                    callback_data=build_task_page_callback(list_id=list_id, page=page - 1),
                )
            )
        pagination_row.append(
            InlineKeyboardButton(
                text=f"{page + 1}/{total_pages}",
                callback_data=TASK_PAGE_NOOP_CALLBACK_DATA,
            )
        )
        if page < total_pages - 1 and list_id is not None:
            pagination_row.append(
                InlineKeyboardButton(
                    text=TASK_NEXT_PAGE_BUTTON_TEXT,
                    callback_data=build_task_page_callback(list_id=list_id, page=page + 1),
                )
            )
        rows.append(pagination_row)

    rows.append(
        [
            InlineKeyboardButton(
                text=START_BUTTONS[0].text,
                callback_data=(
                    build_add_task_to_list_callback(list_id)
                    if list_id
                    else ADD_TASK_CALLBACK_DATA
                ),
            )
        ]
    )
    if list_id is not None and snoozed_count > 0:
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"Отложенные ({snoozed_count})",
                    callback_data=build_task_snoozed_open_callback(list_id),
                )
            ]
        )

    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_snoozed_task_hints_keyboard(
    task_ids: list[int],
    list_id: str,
    buttons_per_row: int = 3,
    page: int = 0,
    total_pages: int = 1,
) -> InlineKeyboardMarkup:
    """Build inline keyboard with snoozed task number hints."""
    rows: list[list[InlineKeyboardButton]] = []
    current_row: list[InlineKeyboardButton] = []
    for task_id in task_ids:
        current_row.append(
            InlineKeyboardButton(
                text=f"#{task_id}",
                callback_data=build_task_snoozed_hint_callback(
                    task_id=task_id,
                    list_id=list_id,
                    page=page,
                ),
            )
        )
        if len(current_row) == buttons_per_row:
            rows.append(current_row)
            current_row = []

    if current_row:
        rows.append(current_row)

    if total_pages > 1:
        pagination_row: list[InlineKeyboardButton] = []
        if page > 0:
            pagination_row.append(
                InlineKeyboardButton(
                    text=TASK_PREVIOUS_PAGE_BUTTON_TEXT,
                    callback_data=build_task_snoozed_page_callback(
                        list_id=list_id,
                        page=page - 1,
                    ),
                )
            )
        pagination_row.append(
            InlineKeyboardButton(
                text=f"{page + 1}/{total_pages}",
                callback_data=TASK_PAGE_NOOP_CALLBACK_DATA,
            )
        )
        if page < total_pages - 1:
            pagination_row.append(
                InlineKeyboardButton(
                    text=TASK_NEXT_PAGE_BUTTON_TEXT,
                    callback_data=build_task_snoozed_page_callback(
                        list_id=list_id,
                        page=page + 1,
                    ),
                )
            )
        rows.append(pagination_row)

    rows.append(
        [
            InlineKeyboardButton(
                text=TASK_BACK_BUTTON_TEXT,
                callback_data=build_task_back_callback(list_id, page=0),
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_selected_task_keyboard(
    task_id: int,
    list_id: str | None = None,
    page: int = 0,
    snoozed_view: bool = False,
) -> InlineKeyboardMarkup:
    """Build inline keyboard for actions with a selected task."""
    effective_list_id = list_id or DEFAULT_TASK_LIST_ID
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=TASK_DONE_BUTTON_TEXT,
                    callback_data=build_task_done_callback(
                        task_id=task_id,
                        list_id=list_id,
                        page=page,
                    ),
                ),
                InlineKeyboardButton(
                    text=TASK_SNOOZE_BUTTON_TEXT,
                    callback_data=build_task_snooze_menu_callback(
                        task_id=task_id,
                        list_id=list_id,
                        page=page,
                    ),
                ),
            ],
            [
                InlineKeyboardButton(
                    text=TASK_DEADLINE_BUTTON_TEXT,
                    callback_data=build_task_deadline_menu_callback(
                        task_id=task_id,
                        list_id=list_id,
                        page=page,
                    ),
                ),
                InlineKeyboardButton(
                    text=TASK_CHANGE_LIST_BUTTON_TEXT,
                    callback_data=build_task_change_list_callback(
                        task_id=task_id,
                        list_id=effective_list_id,
                        page=page,
                    ),
                ),
            ],
            [
                InlineKeyboardButton(
                    text=TASK_RECURRENCE_BUTTON_TEXT,
                    callback_data=build_task_recurrence_menu_callback(
                        task_id=task_id,
                        list_id=list_id,
                        page=page,
                    ),
                ),
            ],
            [
                InlineKeyboardButton(
                    text=TASK_BACK_BUTTON_TEXT,
                    callback_data=(
                        build_task_snoozed_back_callback(list_id, page=page)
                        if snoozed_view and list_id
                        else build_task_back_callback(list_id, page=page)
                        if list_id
                        else TASK_BACK_CALLBACK_DATA
                    ),
                ),
            ]
        ]
    )


def build_selected_task_snooze_keyboard(
    task_id: int,
    list_id: str | None = None,
    page: int = 0,
) -> InlineKeyboardMarkup:
    """Build inline keyboard for snoozing selected task."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=TASK_SNOOZE_EVENING_BUTTON_TEXT,
                    callback_data=build_task_snooze_evening_callback(
                        task_id=task_id,
                        list_id=list_id,
                        page=page,
                    ),
                ),
                InlineKeyboardButton(
                    text=TASK_SNOOZE_TOMORROW_BUTTON_TEXT,
                    callback_data=build_task_snooze_tomorrow_callback(
                        task_id=task_id,
                        list_id=list_id,
                        page=page,
                    ),
                ),
            ],
            [
                InlineKeyboardButton(
                    text=TASK_SNOOZE_WEEKEND_BUTTON_TEXT,
                    callback_data=build_task_snooze_weekend_callback(
                        task_id=task_id,
                        list_id=list_id,
                        page=page,
                    ),
                ),
                InlineKeyboardButton(
                    text=TASK_SNOOZE_NEXT_WEEK_BUTTON_TEXT,
                    callback_data=build_task_snooze_next_week_callback(
                        task_id=task_id,
                        list_id=list_id,
                        page=page,
                    ),
                ),
            ],
            [
                InlineKeyboardButton(
                    text=TASK_SNOOZE_CUSTOM_BUTTON_TEXT,
                    callback_data=build_task_snooze_custom_callback(
                        task_id=task_id,
                        list_id=list_id,
                        page=page,
                    ),
                ),
                InlineKeyboardButton(
                    text=TASK_SNOOZE_REMOVE_BUTTON_TEXT,
                    callback_data=build_task_snooze_remove_callback(
                        task_id=task_id,
                        list_id=list_id,
                        page=page,
                    ),
                ),
            ],
            [
                InlineKeyboardButton(
                    text=TASK_BACK_BUTTON_TEXT,
                    callback_data=(
                        build_task_back_callback(list_id, page=page)
                        if list_id
                        else TASK_BACK_CALLBACK_DATA
                    ),
                )
            ],
        ]
    )


def build_selected_task_recurrence_keyboard(
    task: Task,
    list_id: str | None = None,
    page: int = 0,
) -> InlineKeyboardMarkup:
    """Build inline keyboard for editing selected task recurrence."""
    rows = [
        [
            InlineKeyboardButton(
                text=TASK_RECURRENCE_DAILY_BUTTON_TEXT,
                callback_data=build_task_recurrence_daily_callback(
                    task_id=task.id,
                    list_id=list_id,
                    page=page,
                ),
            ),
            InlineKeyboardButton(
                text=TASK_RECURRENCE_WEEKLY_BUTTON_TEXT,
                callback_data=build_task_recurrence_weekly_callback(
                    task_id=task.id,
                    list_id=list_id,
                    page=page,
                ),
            ),
        ],
        [
            InlineKeyboardButton(
                text=TASK_RECURRENCE_MONTHLY_BUTTON_TEXT,
                callback_data=build_task_recurrence_monthly_callback(
                    task_id=task.id,
                    list_id=list_id,
                    page=page,
                ),
            ),
        ],
    ]
    if task.recurrence is not None:
        rows[-1].append(
            InlineKeyboardButton(
                text=TASK_RECURRENCE_REMOVE_BUTTON_TEXT,
                callback_data=build_task_recurrence_remove_callback(
                    task_id=task.id,
                    list_id=list_id,
                    page=page,
                ),
            )
        )

    rows.append(
        [
            InlineKeyboardButton(
                text=TASK_BACK_BUTTON_TEXT,
                callback_data=(
                    build_task_back_callback(list_id, page=page)
                    if list_id
                    else TASK_BACK_CALLBACK_DATA
                ),
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_selected_task_deadline_keyboard(
    task_id: int,
    list_id: str | None = None,
    page: int = 0,
) -> InlineKeyboardMarkup:
    """Build inline keyboard for editing selected task deadline."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=TASK_DEADLINE_TODAY_BUTTON_TEXT,
                    callback_data=build_task_deadline_today_callback(
                        task_id=task_id,
                        list_id=list_id,
                        page=page,
                    ),
                ),
                InlineKeyboardButton(
                    text=TASK_DEADLINE_TOMORROW_BUTTON_TEXT,
                    callback_data=build_task_deadline_tomorrow_callback(
                        task_id=task_id,
                        list_id=list_id,
                        page=page,
                    ),
                ),
            ],
            [
                InlineKeyboardButton(
                    text=TASK_DEADLINE_CUSTOM_BUTTON_TEXT,
                    callback_data=build_task_deadline_custom_callback(
                        task_id=task_id,
                        list_id=list_id,
                        page=page,
                    ),
                ),
                InlineKeyboardButton(
                    text=TASK_DEADLINE_REMOVE_BUTTON_TEXT,
                    callback_data=build_task_deadline_remove_callback(
                        task_id=task_id,
                        list_id=list_id,
                        page=page,
                    ),
                ),
            ],
            [
                InlineKeyboardButton(
                    text=TASK_BACK_BUTTON_TEXT,
                    callback_data=(
                        build_task_back_callback(list_id, page=page)
                        if list_id
                        else TASK_BACK_CALLBACK_DATA
                    ),
                )
            ],
        ]
    )
