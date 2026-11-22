"""Start-related handlers."""

import logging
from datetime import date, datetime
from typing import Optional

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from easy_task_manager.action_notifications import (
    build_family_member_joined_notification,
    build_family_member_removed_notification,
    build_task_deadline_updated_notification,
    build_task_done_notification,
    build_task_snoozed_notification,
    send_family_action_notification,
)
from easy_task_manager.add_task_contract import (
    ASK_DEADLINE_TIME_TEXT,
    CUSTOM_DEADLINE_INVALID_TEXT,
    CUSTOM_DEADLINE_PROMPT_TEXT,
    CUSTOM_DEADLINE_TIME_INVALID_TEXT,
    DEADLINE_ADDED_TEXT,
    DEADLINE_SKIPPED_TEXT,
    DEADLINE_TIME_ADDED_TEXT,
    DEADLINE_TIME_SKIP_CALLBACK,
)
from easy_task_manager.config import (
    get_configured_family_members,
    get_families_file_path,
    get_family_member_name,
    get_task_lists_file_path,
    get_tasks_file_path,
)
from easy_task_manager.deadline_utils import (
    format_deadline_for_user,
    format_snooze_until_for_user,
    build_snooze_until_for_date,
    get_next_week_snooze,
    get_now_moscow,
    get_today_moscow,
    get_today_evening_snooze,
    get_tomorrow_moscow,
    get_tomorrow_snooze,
    get_weekend_snooze,
    is_past_deadline,
    is_past_deadline_time,
    parse_custom_deadline,
    parse_deadline_time,
)
from easy_task_manager.keyboards import (
    build_change_task_list_keyboard,
    build_deadline_time_keyboard,
    build_family_members_keyboard,
    build_remove_family_member_confirm_keyboard,
    build_task_list_presets_keyboard,
    build_task_lists_keyboard,
    build_family_delete_confirm_keyboard,
    build_family_menu_keyboard,
    build_new_user_keyboard,
    build_selected_task_keyboard,
    build_selected_task_deadline_keyboard,
    build_selected_task_recurrence_keyboard,
    build_selected_task_snooze_keyboard,
    build_start_keyboard,
    build_snoozed_task_hints_keyboard,
    build_task_hints_keyboard,
)
from easy_task_manager.list_tasks_contract import (
    TASK_BACK_CALLBACK_DATA,
    TASK_BACK_CALLBACK_PREFIX,
    TASK_CHANGE_LIST_CALLBACK_PREFIX,
    TASK_DEADLINE_CUSTOM_CALLBACK_PREFIX,
    TASK_DEADLINE_MENU_CALLBACK_PREFIX,
    TASK_DEADLINE_REMOVE_CALLBACK_PREFIX,
    TASK_DEADLINE_TODAY_CALLBACK_PREFIX,
    TASK_DEADLINE_TOMORROW_CALLBACK_PREFIX,
    TASK_DONE_CALLBACK_PREFIX,
    TASK_DONE_TEXT,
    TASK_HINT_CALLBACK_PREFIX,
    TASK_PAGE_CALLBACK_PREFIX,
    TASK_PAGE_NOOP_CALLBACK_DATA,
    TASK_MOVE_TO_LIST_CALLBACK_PREFIX,
    TASK_RECURRING_NEXT_TEMPLATE,
    TASK_RECURRENCE_DAILY_CALLBACK_PREFIX,
    TASK_RECURRENCE_MENU_CALLBACK_PREFIX,
    TASK_RECURRENCE_MONTHLY_CALLBACK_PREFIX,
    TASK_RECURRENCE_NEEDS_DEADLINE_TEXT,
    TASK_RECURRENCE_REMOVE_CALLBACK_PREFIX,
    TASK_RECURRENCE_REMOVED_TEXT,
    TASK_RECURRENCE_UPDATED_TEMPLATE,
    TASK_RECURRENCE_WEEKLY_CALLBACK_PREFIX,
    TASK_SNOOZE_CUSTOM_CALLBACK_PREFIX,
    TASK_SNOOZE_CUSTOM_INVALID_TEXT,
    TASK_SNOOZE_CUSTOM_PROMPT_TEXT,
    TASK_SNOOZE_EVENING_CALLBACK_PREFIX,
    TASK_SNOOZE_MENU_CALLBACK_PREFIX,
    TASK_SNOOZE_NEXT_WEEK_CALLBACK_PREFIX,
    TASK_SNOOZE_REMOVE_CALLBACK_PREFIX,
    TASK_SNOOZE_REMOVED_TEXT,
    TASK_SNOOZE_TOMORROW_CALLBACK_PREFIX,
    TASK_SNOOZE_UPDATED_TEMPLATE,
    TASK_SNOOZE_WEEKEND_CALLBACK_PREFIX,
    TASK_SNOOZED_BACK_CALLBACK_PREFIX,
    TASK_SNOOZED_HINT_CALLBACK_PREFIX,
    TASK_SNOOZED_OPEN_CALLBACK_PREFIX,
    TASK_SNOOZED_PAGE_CALLBACK_PREFIX,
    build_snoozed_task_list_text,
    build_task_list_text,
    build_task_page,
    build_task_page_hint_text,
    parse_task_action_context,
    parse_task_back_context,
    parse_task_hint_context,
    parse_task_move_to_list_callback,
    parse_task_page_callback,
    parse_task_snoozed_back_context,
    parse_task_snoozed_hint_context,
    parse_task_snoozed_page_callback,
)
from easy_task_manager.reminder_wakeup import wake_reminder_scheduler
from easy_task_manager.recurrence import (
    RECURRENCE_DAILY,
    RECURRENCE_MONTHLY,
    RECURRENCE_WEEKLY,
    calculate_next_deadline,
    get_recurrence_label,
)
from easy_task_manager.start_contract import (
    ALREADY_IN_FAMILY_TEXT,
    BACK_TO_START_CALLBACK_DATA,
    CANCEL_REMOVE_FAMILY_MEMBER_CALLBACK_DATA,
    CANCEL_DELETE_FAMILY_CALLBACK_DATA,
    CONFIRM_REMOVE_FAMILY_MEMBER_CALLBACK_PREFIX,
    CONFIRM_DELETE_FAMILY_CALLBACK_DATA,
    CREATE_FAMILY_CALLBACK_DATA,
    DELETE_FAMILY_CALLBACK_DATA,
    FAMILY_DELETED_TEXT,
    FAMILY_DELETE_CANCELLED_TEXT,
    FAMILY_DELETE_CONFIRM_TEXT,
    FAMILY_CREATED_TEXT,
    FAMILY_MEMBER_REMOVE_CANCELLED_TEXT,
    FAMILY_MEMBER_REMOVE_CONFIRM_TEMPLATE,
    FAMILY_MEMBER_REMOVE_FORBIDDEN_TEXT,
    FAMILY_MEMBER_REMOVE_SELF_TEXT,
    FAMILY_MEMBER_REMOVED_TEXT_TEMPLATE,
    FAMILY_MEMBERS_CALLBACK_DATA,
    FAMILY_MEMBERS_NO_REMOVABLE_TEXT,
    FAMILY_MEMBERS_TEXT,
    FAMILY_MENU_CALLBACK_DATA,
    FAMILY_MENU_TEXT,
    HELP_TEXT,
    INVITE_CALLBACK_DATA,
    INVITE_TEXT_TEMPLATE,
    INVITE_TEXT_WITH_LINK_TEMPLATE,
    INVITE_UNAVAILABLE_TEXT,
    JOIN_FAMILY_CALLBACK_DATA,
    JOIN_FAMILY_INVALID_TEXT,
    JOIN_FAMILY_PROMPT_TEXT,
    JOIN_FAMILY_SUCCESS_TEXT,
    JOIN_FAMILY_USED_TEXT,
    LIST_TASKS_CALLBACK_DATA,
    NEW_USER_TEXT,
    REMOVE_FAMILY_MEMBER_CALLBACK_PREFIX,
    TASK_LISTS_CALLBACK_DATA,
    UNKNOWN_USER_TEXT,
    WELCOME_TEXT,
    is_cancel_message,
    is_manual_start_message,
)
from easy_task_manager.family_storage import (
    JOIN_INVITE_ALREADY_MEMBER,
    JOIN_INVITE_INVALID,
    JOIN_INVITE_SUCCESS,
    JOIN_INVITE_USED,
    JsonFamilyStorage,
)
from easy_task_manager.task_storage import DEFAULT_FAMILY_ID, JsonTaskStorage, Task
from easy_task_manager.task_list_storage import (
    DEFAULT_TASK_LIST_ID,
    JsonTaskListStorage,
)
from easy_task_manager.task_lists_contract import (
    CHANGE_TASK_LIST_EMPTY_TEXT,
    CHANGE_TASK_LIST_TEXT,
    TASK_LISTS_ADD_CALLBACK_DATA,
    TASK_LISTS_ADD_TEXT,
    TASK_LISTS_EMPTY_PRESETS_TEXT,
    TASK_LIST_CREATE_CALLBACK_PREFIX,
    TASK_LIST_CREATED_TEMPLATE,
    TASK_LIST_OPEN_CALLBACK_PREFIX,
    TASK_LIST_CHANGED_TEMPLATE,
    build_task_lists_text,
    parse_callback_suffix,
)

logger = logging.getLogger(__name__)
router = Router(name="start-router")
task_storage = JsonTaskStorage(file_path=get_tasks_file_path())
task_list_storage = JsonTaskListStorage(file_path=get_task_lists_file_path())
family_storage = JsonFamilyStorage(file_path=get_families_file_path())


class SelectedTaskDeadlineStates(StatesGroup):
    waiting_custom_deadline = State()
    waiting_deadline_time = State()


class SelectedTaskSnoozeStates(StatesGroup):
    waiting_custom_snooze_until = State()


class FamilyOnboardingStates(StatesGroup):
    waiting_invite_code = State()


def _is_family_message(message: Message) -> bool:
    return _get_family_id_for_chat(message.chat.id) is not None


def _get_family_id_for_chat(chat_id: int) -> Optional[str]:
    return family_storage.get_family_id_for_chat(chat_id=chat_id)


def _get_family_member_display_name(chat_id: int) -> str:
    if family_storage.get_member(chat_id=chat_id) is not None:
        return family_storage.get_member_name(chat_id=chat_id)
    return get_family_member_name(chat_id)


def _get_user_display_name(message: Message) -> str:
    return _get_display_name_from_user(getattr(message, "from_user", None))


def _get_callback_user_display_name(callback: CallbackQuery) -> str:
    return _get_display_name_from_user(getattr(callback, "from_user", None))


def _get_display_name_from_user(user: object) -> str:
    if user is None:
        return "Участник семьи"
    username = str(getattr(user, "username", "") or "").strip()
    if username:
        return username
    full_name = str(getattr(user, "full_name", "") or "").strip()
    if full_name:
        return full_name
    first_name = str(getattr(user, "first_name", "") or "").strip()
    if first_name:
        return first_name
    return "Участник семьи"


def _extract_start_code(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    parts = text.strip().split(maxsplit=1)
    if len(parts) != 2:
        return None
    if parts[0].lower().split("@", 1)[0] not in {"/start", "start"}:
        return None
    return parts[1].strip() or None


def _get_message_family_id(message: Message) -> Optional[str]:
    return _get_family_id_for_chat(message.chat.id)


async def _send_unknown_user_message(message: Message) -> None:
    await message.answer(text=UNKNOWN_USER_TEXT)


async def _ensure_family_access(message: Message) -> bool:
    if _is_family_message(message):
        return True
    await _send_unknown_user_message(message)
    return False


async def _notify_task_action(message: Message, actor_chat_id: int, text: str) -> None:
    bot = getattr(message, "bot", None)
    if bot is None:
        return
    family_id = _get_family_id_for_chat(actor_chat_id)
    if family_id is None:
        return
    await send_family_action_notification(
        bot=bot,
        actor_chat_id=actor_chat_id,
        family_id=family_id,
        text=text,
    )


async def _notify_deadline_updated(message: Message, task: Task) -> None:
    author_name = _get_family_member_display_name(message.chat.id)
    await _notify_task_action(
        message=message,
        actor_chat_id=message.chat.id,
        text=build_task_deadline_updated_notification(author_name, task),
    )


async def _notify_snooze_updated(message: Message, task: Task) -> None:
    author_name = _get_family_member_display_name(message.chat.id)
    await _notify_task_action(
        message=message,
        actor_chat_id=message.chat.id,
        text=build_task_snoozed_notification(author_name, task),
    )


def _create_next_recurring_task(task: Task) -> Optional[Task]:
    if task.deadline is None or task.recurrence is None:
        return None
    next_deadline = calculate_next_deadline(
        deadline=task.deadline,
        recurrence=task.recurrence,
        today=get_today_moscow(),
        anchor_day=task.recurrence_anchor_day,
    )
    if next_deadline is None:
        return None
    return task_storage.add_task(
        chat_id=task.chat_id,
        text=task.text,
        deadline=next_deadline,
        deadline_time=task.deadline_time,
        family_id=task.family_id,
        list_id=task.list_id,
        recurrence=task.recurrence,
        recurrence_anchor_day=task.recurrence_anchor_day,
        note=task.note,
        reminder_enabled=task.reminder_enabled,
    )


async def _notify_family_member_joined(message: Message, member_name: str, family_id: str) -> None:
    bot = getattr(message, "bot", None)
    if bot is None:
        return
    await send_family_action_notification(
        bot=bot,
        actor_chat_id=message.chat.id,
        family_id=family_id,
        text=build_family_member_joined_notification(member_name),
    )


async def _notify_family_member_removed(
    message: Message,
    actor_chat_id: int,
    recipient_chat_ids: tuple[int, ...],
    member_name: str,
) -> None:
    bot = getattr(message, "bot", None)
    if bot is None:
        return
    text = build_family_member_removed_notification(member_name)
    for chat_id in recipient_chat_ids:
        if chat_id == actor_chat_id:
            continue
        try:
            await bot.send_message(chat_id=chat_id, text=text)
        except Exception:
            logger.exception(
                "family_member_removed_notification_failed actor_chat_id=%s recipient_chat_id=%s",
                actor_chat_id,
                chat_id,
            )


def _format_family_members_text(members: tuple[object, ...]) -> str:
    if not members:
        return FAMILY_MEMBERS_TEXT
    lines = [FAMILY_MEMBERS_TEXT]
    for member in members:
        lines.append(f"{getattr(member, 'name', 'Участник семьи')}")
    return "\n".join(lines)


def _parse_chat_id_suffix(callback_data: Optional[str], prefix: str) -> Optional[int]:
    if callback_data is None or not callback_data.startswith(prefix):
        return None
    try:
        return int(callback_data.removeprefix(prefix))
    except ValueError:
        return None


async def _send_task_lists(message: Message) -> None:
    family_id = _get_family_id_for_chat(message.chat.id)
    if family_id is None:
        await _send_unknown_user_message(message)
        return

    task_lists = task_list_storage.list_task_lists_by_family(family_id=family_id)
    task_counts = task_storage.count_tasks_by_family_lists(
        family_id=family_id,
        now=get_now_moscow(),
    )
    await message.answer(
        text=build_task_lists_text(task_lists=task_lists, task_counts=task_counts),
        reply_markup=build_task_lists_keyboard(
            task_lists=task_lists,
            task_counts=task_counts,
        ),
    )


async def _send_family_members(message: Message) -> None:
    family_id = _get_family_id_for_chat(message.chat.id)
    if family_id is None:
        await _send_unknown_user_message(message)
        return

    members = family_storage.list_family_members(family_id=family_id)
    owner_chat_id = family_storage.get_family_owner_chat_id(family_id=family_id)
    text = _format_family_members_text(members)
    if owner_chat_id == message.chat.id and not any(
        member.chat_id != message.chat.id for member in members
    ):
        text = f"{text}\n{FAMILY_MEMBERS_NO_REMOVABLE_TEXT}"
    await message.answer(
        text=text,
        reply_markup=build_family_members_keyboard(
            members=list(members),
            actor_chat_id=message.chat.id,
            owner_chat_id=owner_chat_id,
        ),
    )


async def _notify_family_deleted(
    message: Message,
    actor_chat_id: int,
    member_chat_ids: tuple[int, ...],
) -> None:
    bot = getattr(message, "bot", None)
    if bot is None:
        return

    for chat_id in member_chat_ids:
        if chat_id == actor_chat_id:
            continue
        try:
            await bot.send_message(chat_id=chat_id, text=FAMILY_DELETED_TEXT)
        except Exception:
            logger.exception(
                "family_delete_notification_failed actor_chat_id=%s recipient_chat_id=%s",
                actor_chat_id,
                chat_id,
            )


async def _send_task_list(
    message: Message,
    list_id: str = DEFAULT_TASK_LIST_ID,
    page: int = 0,
) -> None:
    family_id = _get_family_id_for_chat(message.chat.id)
    if family_id is None:
        await _send_unknown_user_message(message)
        return

    task_list = task_list_storage.get_task_list(family_id=family_id, list_id=list_id)
    if task_list is None:
        task_list = task_list_storage.ensure_default_task_list(family_id=family_id)

    tasks = task_storage.list_tasks_by_family_and_list(
        family_id=family_id,
        list_id=task_list.id,
        now=get_now_moscow(),
    )
    snoozed_counts = task_storage.count_snoozed_tasks_by_family_lists(
        family_id=family_id,
        now=get_now_moscow(),
    )
    snoozed_count = snoozed_counts.get(task_list.id, 0)
    if not tasks:
        await message.answer(
            text=build_task_list_text(tasks),
            reply_markup=build_task_hints_keyboard(
                task_ids=[],
                list_id=task_list.id,
                snoozed_count=snoozed_count,
            ),
        )
        return

    task_page = build_task_page(tasks=tasks, page=page)
    await message.answer(text=build_task_list_text(task_page.tasks))
    await message.answer(
        text=build_task_page_hint_text(
            page=task_page.page,
            total_pages=task_page.total_pages,
        ),
        reply_markup=build_task_hints_keyboard(
            task_ids=[task.id for task in task_page.tasks],
            list_id=task_list.id,
            page=task_page.page,
            total_pages=task_page.total_pages,
            snoozed_count=snoozed_count,
        ),
    )


async def _send_snoozed_task_list(
    message: Message,
    list_id: str = DEFAULT_TASK_LIST_ID,
    page: int = 0,
) -> None:
    family_id = _get_family_id_for_chat(message.chat.id)
    if family_id is None:
        await _send_unknown_user_message(message)
        return

    task_list = task_list_storage.get_task_list(family_id=family_id, list_id=list_id)
    if task_list is None:
        task_list = task_list_storage.ensure_default_task_list(family_id=family_id)

    tasks = task_storage.list_snoozed_tasks_by_family_and_list(
        family_id=family_id,
        list_id=task_list.id,
        now=get_now_moscow(),
    )
    if not tasks:
        await message.answer(
            text=build_snoozed_task_list_text(tasks),
            reply_markup=build_snoozed_task_hints_keyboard(
                task_ids=[],
                list_id=task_list.id,
            ),
        )
        return

    task_page = build_task_page(tasks=tasks, page=page)
    await message.answer(text=build_snoozed_task_list_text(task_page.tasks))
    await message.answer(
        text=build_task_page_hint_text(
            page=task_page.page,
            total_pages=task_page.total_pages,
        ),
        reply_markup=build_snoozed_task_hints_keyboard(
            task_ids=[task.id for task in task_page.tasks],
            list_id=task_list.id,
            page=task_page.page,
            total_pages=task_page.total_pages,
        ),
    )


async def _send_selected_task(
    message: Message,
    task_id: int,
    page: int = 0,
    list_id: Optional[str] = None,
    snoozed_view: bool = False,
) -> bool:
    family_id = _get_family_id_for_chat(message.chat.id)
    if family_id is None:
        await _send_unknown_user_message(message)
        return False

    selected_task = task_storage.get_task_by_family(family_id=family_id, task_id=task_id)
    if selected_task is None:
        await _send_task_list(message=message)
        return False

    await message.answer(
        text=build_task_list_text([selected_task]),
        reply_markup=build_selected_task_keyboard(
            task_id=selected_task.id,
            list_id=list_id or selected_task.list_id,
            page=page,
            snoozed_view=snoozed_view,
        ),
    )
    return True


async def _ask_selected_task_deadline_time(
    message: Message,
    state: FSMContext,
    task_id: int,
    deadline: date,
    list_id: Optional[str] = None,
    page: int = 0,
) -> None:
    selected_task = task_storage.get_task_by_family(
        family_id=_get_family_id_for_chat(message.chat.id) or DEFAULT_FAMILY_ID,
        task_id=task_id,
    )
    if selected_task is None:
        await state.clear()
        await _send_task_list(message=message)
        return

    await state.update_data(
        selected_deadline_task_id=task_id,
        selected_deadline_list_id=list_id,
        selected_deadline_page=page,
        pending_deadline=deadline.isoformat(),
    )
    await state.set_state(SelectedTaskDeadlineStates.waiting_deadline_time)
    await message.answer(text=DEADLINE_ADDED_TEXT)
    await message.answer(
        text=ASK_DEADLINE_TIME_TEXT,
        reply_markup=build_deadline_time_keyboard(),
    )


def _get_pending_deadline(data: dict[str, object]) -> Optional[date]:
    raw_deadline = data.get("pending_deadline")
    if not raw_deadline:
        return None
    try:
        return date.fromisoformat(str(raw_deadline))
    except ValueError:
        return None


def _get_selected_deadline_task_id(data: dict[str, object]) -> Optional[int]:
    raw_task_id = data.get("selected_deadline_task_id")
    if raw_task_id is None:
        return None
    try:
        return int(raw_task_id)
    except (TypeError, ValueError):
        return None


def _get_selected_deadline_list_id(data: dict[str, object]) -> Optional[str]:
    raw_list_id = str(data.get("selected_deadline_list_id") or "").strip()
    return raw_list_id or None


def _get_selected_deadline_page(data: dict[str, object]) -> int:
    try:
        return max(int(data.get("selected_deadline_page") or 0), 0)
    except (TypeError, ValueError):
        return 0


def _get_selected_snooze_task_id(data: dict[str, object]) -> Optional[int]:
    raw_task_id = data.get("selected_snooze_task_id")
    if raw_task_id is None:
        return None
    try:
        return int(raw_task_id)
    except (TypeError, ValueError):
        return None


def _get_selected_snooze_list_id(data: dict[str, object]) -> Optional[str]:
    raw_list_id = str(data.get("selected_snooze_list_id") or "").strip()
    return raw_list_id or None


def _get_selected_snooze_page(data: dict[str, object]) -> int:
    try:
        return max(int(data.get("selected_snooze_page") or 0), 0)
    except (TypeError, ValueError):
        return 0


async def _cancel_to_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await send_start_message(message=message, source="cancel_text")


async def send_start_message(message: Message, source: str) -> None:
    from_user = getattr(message, "from_user", None)
    logger.info(
        "start_received source=%s user_id=%s chat_id=%s",
        source,
        from_user.id if from_user else None,
        message.chat.id,
    )
    start_code = _extract_start_code(getattr(message, "text", None))
    family_id = _get_family_id_for_chat(message.chat.id)
    if family_id is None and start_code is not None:
        status, _member = family_storage.join_family_by_invite(
            chat_id=message.chat.id,
            name=_get_user_display_name(message),
            code=start_code,
        )
        if status == JOIN_INVITE_SUCCESS:
            await message.answer(text=JOIN_FAMILY_SUCCESS_TEXT)
            if _member is not None:
                await _notify_family_member_joined(
                    message=message,
                    member_name=getattr(_member, "name", _get_user_display_name(message)),
                    family_id=getattr(_member, "family_id", DEFAULT_FAMILY_ID),
                )
            await message.answer(text=WELCOME_TEXT, reply_markup=build_start_keyboard())
            return
        if status == JOIN_INVITE_USED:
            await message.answer(text=JOIN_FAMILY_USED_TEXT)
            return
        if status == JOIN_INVITE_INVALID:
            await message.answer(text=JOIN_FAMILY_INVALID_TEXT)
            return

    if family_id is None:
        await message.answer(text=NEW_USER_TEXT, reply_markup=build_new_user_keyboard())
        return

    if start_code is not None:
        await message.answer(text=ALREADY_IN_FAMILY_TEXT)

    await message.answer(text=WELCOME_TEXT, reply_markup=build_start_keyboard())
    logger.info(
        "start_sent source=%s user_id=%s chat_id=%s",
        source,
        from_user.id if from_user else None,
        message.chat.id,
    )


@router.message(CommandStart(), F.chat.type == "private")
async def handle_command_start(message: Message) -> None:
    await send_start_message(message=message, source="/start")


@router.message(Command("menu"), F.chat.type == "private")
async def handle_menu_command(message: Message, state: FSMContext) -> None:
    await state.clear()
    await send_start_message(message=message, source="/menu")


@router.message(Command("lists"), F.chat.type == "private")
async def handle_lists_command(message: Message, state: FSMContext) -> None:
    await state.clear()
    await _send_task_lists(message=message)


@router.message(Command("family"), F.chat.type == "private")
async def handle_family_command(message: Message, state: FSMContext) -> None:
    await state.clear()
    if not await _ensure_family_access(message):
        return

    await message.answer(
        text=FAMILY_MENU_TEXT,
        reply_markup=build_family_menu_keyboard(),
    )


@router.message(Command("help"), F.chat.type == "private")
async def handle_help_command(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(text=HELP_TEXT)


@router.callback_query(F.data == CREATE_FAMILY_CALLBACK_DATA, F.message.chat.type == "private")
async def handle_create_family_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    if callback.message is None:
        return
    if _get_message_family_id(callback.message) is not None:
        await callback.message.answer(text=ALREADY_IN_FAMILY_TEXT)
        await callback.message.answer(text=WELCOME_TEXT, reply_markup=build_start_keyboard())
        return

    family_storage.create_family_for_member(
        chat_id=callback.message.chat.id,
        name=_get_callback_user_display_name(callback),
    )
    await callback.message.answer(text=FAMILY_CREATED_TEXT)
    await callback.message.answer(text=WELCOME_TEXT, reply_markup=build_start_keyboard())


@router.callback_query(F.data == JOIN_FAMILY_CALLBACK_DATA, F.message.chat.type == "private")
async def handle_join_family_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if callback.message is None:
        return
    if _get_message_family_id(callback.message) is not None:
        await state.clear()
        await callback.message.answer(text=ALREADY_IN_FAMILY_TEXT)
        await callback.message.answer(text=WELCOME_TEXT, reply_markup=build_start_keyboard())
        return

    await state.set_state(FamilyOnboardingStates.waiting_invite_code)
    await callback.message.answer(text=JOIN_FAMILY_PROMPT_TEXT)


@router.message(FamilyOnboardingStates.waiting_invite_code, F.chat.type == "private", F.text)
async def handle_join_family_code(message: Message, state: FSMContext) -> None:
    if is_cancel_message(message.text):
        await _cancel_to_start(message=message, state=state)
        return

    status, _member = family_storage.join_family_by_invite(
        chat_id=message.chat.id,
        name=_get_user_display_name(message),
        code=message.text,
    )
    if status == JOIN_INVITE_SUCCESS:
        await state.clear()
        await message.answer(text=JOIN_FAMILY_SUCCESS_TEXT)
        if _member is not None:
            await _notify_family_member_joined(
                message=message,
                member_name=getattr(_member, "name", _get_user_display_name(message)),
                family_id=getattr(_member, "family_id", DEFAULT_FAMILY_ID),
            )
        await message.answer(text=WELCOME_TEXT, reply_markup=build_start_keyboard())
        return
    if status == JOIN_INVITE_ALREADY_MEMBER:
        await state.clear()
        await message.answer(text=ALREADY_IN_FAMILY_TEXT)
        await message.answer(text=WELCOME_TEXT, reply_markup=build_start_keyboard())
        return
    if status == JOIN_INVITE_USED:
        await message.answer(text=JOIN_FAMILY_USED_TEXT)
        return

    await message.answer(text=JOIN_FAMILY_INVALID_TEXT)


@router.callback_query(F.data == INVITE_CALLBACK_DATA, F.message.chat.type == "private")
async def handle_invite_callback(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message is None:
        return
    if not await _ensure_family_access(callback.message):
        return

    invite = family_storage.create_invite(created_by_chat_id=callback.message.chat.id)
    if invite is None:
        await callback.message.answer(text=INVITE_UNAVAILABLE_TEXT)
        return

    bot_username = await _get_bot_username(callback.message)
    if bot_username:
        text = INVITE_TEXT_WITH_LINK_TEMPLATE.format(
            code=invite.code,
            link=f"https://t.me/{bot_username}?start={invite.code}",
        )
    else:
        text = INVITE_TEXT_TEMPLATE.format(code=invite.code)
    await callback.message.answer(text=text)


@router.callback_query(F.data == FAMILY_MENU_CALLBACK_DATA, F.message.chat.type == "private")
async def handle_family_menu_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    if callback.message is None:
        return
    if not await _ensure_family_access(callback.message):
        return

    await callback.message.answer(
        text=FAMILY_MENU_TEXT,
        reply_markup=build_family_menu_keyboard(),
    )


@router.callback_query(F.data == FAMILY_MEMBERS_CALLBACK_DATA, F.message.chat.type == "private")
async def handle_family_members_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    if callback.message is None:
        return
    if not await _ensure_family_access(callback.message):
        return

    await _send_family_members(message=callback.message)


@router.callback_query(
    F.data.startswith(REMOVE_FAMILY_MEMBER_CALLBACK_PREFIX),
    F.message.chat.type == "private",
)
async def handle_remove_family_member_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    if callback.message is None:
        return

    family_id = _get_message_family_id(callback.message)
    if family_id is None:
        await _send_unknown_user_message(callback.message)
        return

    owner_chat_id = family_storage.get_family_owner_chat_id(family_id=family_id)
    if owner_chat_id != callback.message.chat.id:
        await callback.message.answer(text=FAMILY_MEMBER_REMOVE_FORBIDDEN_TEXT)
        return

    member_chat_id = _parse_chat_id_suffix(
        callback.data,
        REMOVE_FAMILY_MEMBER_CALLBACK_PREFIX,
    )
    if member_chat_id is None:
        await _send_family_members(message=callback.message)
        return
    if member_chat_id == callback.message.chat.id:
        await callback.message.answer(text=FAMILY_MEMBER_REMOVE_SELF_TEXT)
        return

    member = family_storage.get_member(chat_id=member_chat_id)
    if member is None or member.family_id != family_id:
        await _send_family_members(message=callback.message)
        return

    await callback.message.answer(
        text=FAMILY_MEMBER_REMOVE_CONFIRM_TEMPLATE.format(name=member.name),
        reply_markup=build_remove_family_member_confirm_keyboard(member_chat_id),
    )


@router.callback_query(
    F.data == CANCEL_REMOVE_FAMILY_MEMBER_CALLBACK_DATA,
    F.message.chat.type == "private",
)
async def handle_cancel_remove_family_member_callback(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    await callback.answer()
    await state.clear()
    if callback.message is None:
        return
    if not await _ensure_family_access(callback.message):
        return

    await callback.message.answer(text=FAMILY_MEMBER_REMOVE_CANCELLED_TEXT)
    await _send_family_members(message=callback.message)


@router.callback_query(
    F.data.startswith(CONFIRM_REMOVE_FAMILY_MEMBER_CALLBACK_PREFIX),
    F.message.chat.type == "private",
)
async def handle_confirm_remove_family_member_callback(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    await callback.answer()
    await state.clear()
    if callback.message is None:
        return

    family_id = _get_message_family_id(callback.message)
    if family_id is None:
        await _send_unknown_user_message(callback.message)
        return

    owner_chat_id = family_storage.get_family_owner_chat_id(family_id=family_id)
    if owner_chat_id != callback.message.chat.id:
        await callback.message.answer(text=FAMILY_MEMBER_REMOVE_FORBIDDEN_TEXT)
        return

    member_chat_id = _parse_chat_id_suffix(
        callback.data,
        CONFIRM_REMOVE_FAMILY_MEMBER_CALLBACK_PREFIX,
    )
    if member_chat_id is None:
        await _send_family_members(message=callback.message)
        return
    if member_chat_id == callback.message.chat.id:
        await callback.message.answer(text=FAMILY_MEMBER_REMOVE_SELF_TEXT)
        return

    members_before = family_storage.list_family_chat_ids(family_id=family_id)
    removed_member = family_storage.remove_member(
        family_id=family_id,
        chat_id=member_chat_id,
    )
    if removed_member is None:
        await _send_family_members(message=callback.message)
        return

    notification_recipients = tuple(
        chat_id for chat_id in members_before if chat_id != callback.message.chat.id
    )
    await callback.message.answer(
        text=FAMILY_MEMBER_REMOVED_TEXT_TEMPLATE.format(name=removed_member.name)
    )
    await _notify_family_member_removed(
        message=callback.message,
        actor_chat_id=callback.message.chat.id,
        recipient_chat_ids=notification_recipients,
        member_name=removed_member.name,
    )
    await _send_family_members(message=callback.message)


@router.callback_query(F.data == DELETE_FAMILY_CALLBACK_DATA, F.message.chat.type == "private")
async def handle_delete_family_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    if callback.message is None:
        return
    if not await _ensure_family_access(callback.message):
        return

    await callback.message.answer(
        text=FAMILY_DELETE_CONFIRM_TEXT,
        reply_markup=build_family_delete_confirm_keyboard(),
    )


@router.callback_query(
    F.data == CANCEL_DELETE_FAMILY_CALLBACK_DATA,
    F.message.chat.type == "private",
)
async def handle_cancel_delete_family_callback(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    await callback.answer()
    await state.clear()
    if callback.message is None:
        return
    if not await _ensure_family_access(callback.message):
        return

    await callback.message.answer(text=FAMILY_DELETE_CANCELLED_TEXT)
    await callback.message.answer(
        text=FAMILY_MENU_TEXT,
        reply_markup=build_family_menu_keyboard(),
    )


@router.callback_query(
    F.data == CONFIRM_DELETE_FAMILY_CALLBACK_DATA,
    F.message.chat.type == "private",
)
async def handle_confirm_delete_family_callback(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    await callback.answer()
    await state.clear()
    if callback.message is None:
        return

    family_id = _get_message_family_id(callback.message)
    if family_id is None:
        await _send_unknown_user_message(callback.message)
        return

    member_chat_ids = family_storage.delete_family(family_id=family_id)
    deleted_task_count = task_storage.delete_tasks_by_family(family_id=family_id)
    task_list_storage.delete_task_lists_by_family(family_id=family_id)
    if deleted_task_count:
        wake_reminder_scheduler("family_deleted")

    await callback.message.answer(text=FAMILY_DELETED_TEXT)
    await _notify_family_deleted(
        message=callback.message,
        actor_chat_id=callback.message.chat.id,
        member_chat_ids=member_chat_ids,
    )
    logger.info(
        "family_deleted family_id=%s actor_chat_id=%s member_count=%s task_count=%s",
        family_id,
        callback.message.chat.id,
        len(member_chat_ids),
        deleted_task_count,
    )
    await callback.message.answer(text=NEW_USER_TEXT, reply_markup=build_new_user_keyboard())


@router.callback_query(F.data == BACK_TO_START_CALLBACK_DATA, F.message.chat.type == "private")
async def handle_back_to_start_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    if callback.message is None:
        return
    await send_start_message(message=callback.message, source="back_to_start")


async def _get_bot_username(message: Message) -> Optional[str]:
    bot = getattr(message, "bot", None)
    if bot is None:
        return None
    get_me = getattr(bot, "get_me", None)
    if get_me is None:
        return None
    try:
        me = await get_me()
    except Exception:
        logger.exception("bot_username_lookup_failed chat_id=%s", message.chat.id)
        return None
    username = str(getattr(me, "username", "") or "").strip()
    return username or None


@router.message(
    SelectedTaskDeadlineStates.waiting_custom_deadline,
    F.chat.type == "private",
    F.text,
)
async def handle_selected_task_custom_deadline(message: Message, state: FSMContext) -> None:
    if not await _ensure_family_access(message):
        await state.clear()
        return

    if is_cancel_message(message.text):
        await _cancel_to_start(message=message, state=state)
        return

    data = await state.get_data()
    task_id = _get_selected_deadline_task_id(data)
    if task_id is None:
        await state.clear()
        await _send_task_list(message=message)
        return

    try:
        parsed_date = parse_custom_deadline(message.text)
    except ValueError:
        await message.answer(text=CUSTOM_DEADLINE_INVALID_TEXT)
        return

    if is_past_deadline(parsed_date):
        await message.answer(text=CUSTOM_DEADLINE_INVALID_TEXT)
        return

    await _ask_selected_task_deadline_time(
        message=message,
        state=state,
        task_id=task_id,
        deadline=parsed_date,
        list_id=_get_selected_deadline_list_id(data),
        page=_get_selected_deadline_page(data),
    )


@router.message(
    SelectedTaskDeadlineStates.waiting_deadline_time,
    F.chat.type == "private",
    F.text,
)
async def handle_selected_task_deadline_time(message: Message, state: FSMContext) -> None:
    if not await _ensure_family_access(message):
        await state.clear()
        return

    if is_cancel_message(message.text):
        await _cancel_to_start(message=message, state=state)
        return

    data = await state.get_data()
    task_id = _get_selected_deadline_task_id(data)
    pending_deadline = _get_pending_deadline(data)
    list_id = _get_selected_deadline_list_id(data)
    page = _get_selected_deadline_page(data)
    if task_id is None or pending_deadline is None:
        await state.clear()
        await _send_task_list(message=message)
        return

    try:
        parsed_time = parse_deadline_time(message.text)
    except ValueError:
        await message.answer(text=CUSTOM_DEADLINE_TIME_INVALID_TEXT)
        return

    if is_past_deadline_time(pending_deadline, parsed_time):
        await message.answer(text=CUSTOM_DEADLINE_TIME_INVALID_TEXT)
        return

    updated = task_storage.update_task_deadline_by_family(
        family_id=_get_message_family_id(message) or DEFAULT_FAMILY_ID,
        task_id=task_id,
        deadline=pending_deadline,
        deadline_time=parsed_time,
    )
    await state.clear()
    if not updated:
        await _send_task_list(
            message=message,
            list_id=list_id or DEFAULT_TASK_LIST_ID,
            page=page,
        )
        return

    await message.answer(text=DEADLINE_TIME_ADDED_TEXT)
    wake_reminder_scheduler("task_deadline_updated")
    await _notify_deadline_updated(message=message, task=updated)
    await _send_selected_task(
        message=message,
        task_id=task_id,
        list_id=list_id,
        page=page,
    )


@router.message(
    SelectedTaskSnoozeStates.waiting_custom_snooze_until,
    F.chat.type == "private",
    F.text,
)
async def handle_selected_task_custom_snooze(message: Message, state: FSMContext) -> None:
    if not await _ensure_family_access(message):
        await state.clear()
        return

    if is_cancel_message(message.text):
        await _cancel_to_start(message=message, state=state)
        return

    data = await state.get_data()
    task_id = _get_selected_snooze_task_id(data)
    list_id = _get_selected_snooze_list_id(data)
    page = _get_selected_snooze_page(data)
    if task_id is None:
        await state.clear()
        await _send_task_list(
            message=message,
            list_id=list_id or DEFAULT_TASK_LIST_ID,
            page=page,
        )
        return

    try:
        parsed_date = parse_custom_deadline(message.text)
    except ValueError:
        await message.answer(text=TASK_SNOOZE_CUSTOM_INVALID_TEXT)
        return

    if is_past_deadline(parsed_date):
        await message.answer(text=TASK_SNOOZE_CUSTOM_INVALID_TEXT)
        return

    snoozed_until = build_snooze_until_for_date(parsed_date)
    updated = task_storage.update_task_snooze_by_family(
        family_id=_get_message_family_id(message) or DEFAULT_FAMILY_ID,
        task_id=task_id,
        snoozed_until=snoozed_until,
    )
    await state.clear()
    if updated is None:
        await _send_task_list(
            message=message,
            list_id=list_id or DEFAULT_TASK_LIST_ID,
            page=page,
        )
        return

    await message.answer(
        text=TASK_SNOOZE_UPDATED_TEMPLATE.format(
            snoozed_until=format_snooze_until_for_user(snoozed_until)
        )
    )
    await _notify_snooze_updated(message=message, task=updated)
    await _send_task_list(
        message=message,
        list_id=list_id or updated.list_id,
        page=page,
    )


@router.message(F.chat.type == "private")
async def handle_manual_start(message: Message, state: Optional[FSMContext] = None) -> None:
    if is_cancel_message(message.text):
        if state is not None:
            await state.clear()
        await send_start_message(message=message, source="cancel_text")
        return
    if not is_manual_start_message(message.text):
        return
    await send_start_message(message=message, source="start_text")


@router.callback_query(F.data == LIST_TASKS_CALLBACK_DATA, F.message.chat.type == "private")
async def handle_list_callback(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message is None:
        return
    if not await _ensure_family_access(callback.message):
        return

    await _send_task_list(message=callback.message)


@router.callback_query(F.data == TASK_LISTS_CALLBACK_DATA, F.message.chat.type == "private")
async def handle_task_lists_callback(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message is None:
        return
    if not await _ensure_family_access(callback.message):
        return

    await _send_task_lists(message=callback.message)


@router.callback_query(F.data == TASK_LISTS_ADD_CALLBACK_DATA, F.message.chat.type == "private")
async def handle_task_lists_add_callback(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message is None:
        return
    if not await _ensure_family_access(callback.message):
        return

    family_id = _get_message_family_id(callback.message) or DEFAULT_FAMILY_ID
    presets = task_list_storage.list_missing_presets_by_family(family_id=family_id)
    if not presets:
        await callback.message.answer(text=TASK_LISTS_EMPTY_PRESETS_TEXT)
        await _send_task_lists(message=callback.message)
        return

    await callback.message.answer(
        text=TASK_LISTS_ADD_TEXT,
        reply_markup=build_task_list_presets_keyboard(presets=presets),
    )


@router.callback_query(
    F.data.startswith(TASK_LIST_CREATE_CALLBACK_PREFIX),
    F.message.chat.type == "private",
)
async def handle_task_list_create_callback(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message is None:
        return
    if not await _ensure_family_access(callback.message):
        return

    preset_id = parse_callback_suffix(callback.data, TASK_LIST_CREATE_CALLBACK_PREFIX)
    family_id = _get_message_family_id(callback.message) or DEFAULT_FAMILY_ID
    task_list = (
        task_list_storage.create_task_list_from_preset(
            family_id=family_id,
            preset_id=preset_id,
        )
        if preset_id is not None
        else None
    )
    if task_list is None:
        await _send_task_lists(message=callback.message)
        return

    await callback.message.answer(
        text=TASK_LIST_CREATED_TEMPLATE.format(title=task_list.title)
    )
    await _send_task_lists(message=callback.message)


@router.callback_query(
    F.data.startswith(TASK_LIST_OPEN_CALLBACK_PREFIX),
    F.message.chat.type == "private",
)
async def handle_task_list_open_callback(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message is None:
        return
    if not await _ensure_family_access(callback.message):
        return

    list_id = parse_callback_suffix(callback.data, TASK_LIST_OPEN_CALLBACK_PREFIX)
    await _send_task_list(
        message=callback.message,
        list_id=list_id or DEFAULT_TASK_LIST_ID,
    )


@router.callback_query(F.data == TASK_PAGE_NOOP_CALLBACK_DATA, F.message.chat.type == "private")
async def handle_task_page_noop_callback(callback: CallbackQuery) -> None:
    await callback.answer()


@router.callback_query(F.data.startswith(TASK_PAGE_CALLBACK_PREFIX), F.message.chat.type == "private")
async def handle_task_page_callback(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message is None:
        return
    if not await _ensure_family_access(callback.message):
        return

    page, list_id = parse_task_page_callback(callback.data)
    await _send_task_list(
        message=callback.message,
        list_id=list_id or DEFAULT_TASK_LIST_ID,
        page=page or 0,
    )


@router.callback_query(
    F.data.startswith(TASK_SNOOZED_OPEN_CALLBACK_PREFIX),
    F.message.chat.type == "private",
)
async def handle_task_snoozed_open_callback(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message is None:
        return
    if not await _ensure_family_access(callback.message):
        return

    list_id = callback.data.removeprefix(TASK_SNOOZED_OPEN_CALLBACK_PREFIX)
    await _send_snoozed_task_list(
        message=callback.message,
        list_id=list_id or DEFAULT_TASK_LIST_ID,
    )


@router.callback_query(
    F.data.startswith(TASK_SNOOZED_PAGE_CALLBACK_PREFIX),
    F.message.chat.type == "private",
)
async def handle_task_snoozed_page_callback(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message is None:
        return
    if not await _ensure_family_access(callback.message):
        return

    page, list_id = parse_task_snoozed_page_callback(callback.data)
    await _send_snoozed_task_list(
        message=callback.message,
        list_id=list_id or DEFAULT_TASK_LIST_ID,
        page=page or 0,
    )


@router.callback_query(F.data.startswith(TASK_HINT_CALLBACK_PREFIX), F.message.chat.type == "private")
async def handle_task_hint_callback(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message is None:
        return
    if not await _ensure_family_access(callback.message):
        return

    task_id, page, list_id = parse_task_hint_context(callback.data)
    family_id = _get_message_family_id(callback.message) or DEFAULT_FAMILY_ID
    selected_task = task_storage.get_task_by_family(family_id=family_id, task_id=task_id)
    if selected_task is None:
        await _send_task_list(
            message=callback.message,
            list_id=list_id or DEFAULT_TASK_LIST_ID,
            page=page or 0,
        )
        return

    await callback.message.answer(
        text=build_task_list_text([selected_task]),
        reply_markup=build_selected_task_keyboard(
            task_id=selected_task.id,
            list_id=list_id or selected_task.list_id,
            page=page or 0,
        ),
    )


@router.callback_query(
    F.data.startswith(TASK_SNOOZED_HINT_CALLBACK_PREFIX),
    F.message.chat.type == "private",
)
async def handle_task_snoozed_hint_callback(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message is None:
        return
    if not await _ensure_family_access(callback.message):
        return

    task_id, page, list_id = parse_task_snoozed_hint_context(callback.data)
    family_id = _get_message_family_id(callback.message) or DEFAULT_FAMILY_ID
    selected_task = task_storage.get_task_by_family(family_id=family_id, task_id=task_id)
    if selected_task is None:
        await _send_snoozed_task_list(
            message=callback.message,
            list_id=list_id or DEFAULT_TASK_LIST_ID,
            page=page or 0,
        )
        return

    await callback.message.answer(
        text=build_task_list_text([selected_task]),
        reply_markup=build_selected_task_keyboard(
            task_id=selected_task.id,
            list_id=list_id or selected_task.list_id,
            page=page or 0,
            snoozed_view=True,
        ),
    )


@router.callback_query(
    F.data.startswith(TASK_DEADLINE_MENU_CALLBACK_PREFIX),
    F.message.chat.type == "private",
)
async def handle_task_deadline_menu_callback(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message is None:
        return
    if not await _ensure_family_access(callback.message):
        return

    task_id, page, list_id = parse_task_action_context(
        callback.data,
        TASK_DEADLINE_MENU_CALLBACK_PREFIX,
    )
    family_id = _get_message_family_id(callback.message) or DEFAULT_FAMILY_ID
    selected_task = task_storage.get_task_by_family(family_id=family_id, task_id=task_id)
    if selected_task is None:
        await _send_task_list(
            message=callback.message,
            list_id=list_id or DEFAULT_TASK_LIST_ID,
            page=page or 0,
        )
        return

    await callback.message.answer(
        text=build_task_list_text([selected_task]),
        reply_markup=build_selected_task_deadline_keyboard(
            task_id=selected_task.id,
            list_id=list_id or selected_task.list_id,
            page=page or 0,
        ),
    )


@router.callback_query(
    F.data.startswith(TASK_SNOOZE_MENU_CALLBACK_PREFIX),
    F.message.chat.type == "private",
)
async def handle_task_snooze_menu_callback(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message is None:
        return
    if not await _ensure_family_access(callback.message):
        return

    task_id, page, list_id = parse_task_action_context(
        callback.data,
        TASK_SNOOZE_MENU_CALLBACK_PREFIX,
    )
    family_id = _get_message_family_id(callback.message) or DEFAULT_FAMILY_ID
    selected_task = task_storage.get_task_by_family(family_id=family_id, task_id=task_id)
    if selected_task is None:
        await _send_task_list(
            message=callback.message,
            list_id=list_id or DEFAULT_TASK_LIST_ID,
            page=page or 0,
        )
        return

    await callback.message.answer(
        text=build_task_list_text([selected_task]),
        reply_markup=build_selected_task_snooze_keyboard(
            task_id=selected_task.id,
            list_id=list_id or selected_task.list_id,
            page=page or 0,
        ),
    )


async def _handle_task_snooze_update(
    callback: CallbackQuery,
    prefix: str,
    snoozed_until: Optional[datetime],
) -> None:
    await callback.answer()
    if callback.message is None:
        return
    if not await _ensure_family_access(callback.message):
        return

    task_id, page, list_id = parse_task_action_context(callback.data, prefix)
    if task_id is None:
        await _send_task_list(message=callback.message)
        return

    updated_task = task_storage.update_task_snooze_by_family(
        family_id=_get_message_family_id(callback.message) or DEFAULT_FAMILY_ID,
        task_id=task_id,
        snoozed_until=snoozed_until,
    )
    if updated_task is None:
        await _send_task_list(
            message=callback.message,
            list_id=list_id or DEFAULT_TASK_LIST_ID,
            page=page or 0,
        )
        return

    if updated_task.snoozed_until is None:
        await callback.message.answer(text=TASK_SNOOZE_REMOVED_TEXT)
    else:
        await callback.message.answer(
            text=TASK_SNOOZE_UPDATED_TEMPLATE.format(
                snoozed_until=format_snooze_until_for_user(updated_task.snoozed_until)
            )
        )
    await _notify_snooze_updated(message=callback.message, task=updated_task)
    await _send_task_list(
        message=callback.message,
        list_id=list_id or updated_task.list_id,
        page=page or 0,
    )


@router.callback_query(
    F.data.startswith(TASK_SNOOZE_EVENING_CALLBACK_PREFIX),
    F.message.chat.type == "private",
)
async def handle_task_snooze_evening_callback(callback: CallbackQuery) -> None:
    await _handle_task_snooze_update(
        callback=callback,
        prefix=TASK_SNOOZE_EVENING_CALLBACK_PREFIX,
        snoozed_until=get_today_evening_snooze(),
    )


@router.callback_query(
    F.data.startswith(TASK_SNOOZE_TOMORROW_CALLBACK_PREFIX),
    F.message.chat.type == "private",
)
async def handle_task_snooze_tomorrow_callback(callback: CallbackQuery) -> None:
    await _handle_task_snooze_update(
        callback=callback,
        prefix=TASK_SNOOZE_TOMORROW_CALLBACK_PREFIX,
        snoozed_until=get_tomorrow_snooze(),
    )


@router.callback_query(
    F.data.startswith(TASK_SNOOZE_WEEKEND_CALLBACK_PREFIX),
    F.message.chat.type == "private",
)
async def handle_task_snooze_weekend_callback(callback: CallbackQuery) -> None:
    await _handle_task_snooze_update(
        callback=callback,
        prefix=TASK_SNOOZE_WEEKEND_CALLBACK_PREFIX,
        snoozed_until=get_weekend_snooze(),
    )


@router.callback_query(
    F.data.startswith(TASK_SNOOZE_NEXT_WEEK_CALLBACK_PREFIX),
    F.message.chat.type == "private",
)
async def handle_task_snooze_next_week_callback(callback: CallbackQuery) -> None:
    await _handle_task_snooze_update(
        callback=callback,
        prefix=TASK_SNOOZE_NEXT_WEEK_CALLBACK_PREFIX,
        snoozed_until=get_next_week_snooze(),
    )


@router.callback_query(
    F.data.startswith(TASK_SNOOZE_REMOVE_CALLBACK_PREFIX),
    F.message.chat.type == "private",
)
async def handle_task_snooze_remove_callback(callback: CallbackQuery) -> None:
    await _handle_task_snooze_update(
        callback=callback,
        prefix=TASK_SNOOZE_REMOVE_CALLBACK_PREFIX,
        snoozed_until=None,
    )


@router.callback_query(
    F.data.startswith(TASK_SNOOZE_CUSTOM_CALLBACK_PREFIX),
    F.message.chat.type == "private",
)
async def handle_task_snooze_custom_callback(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    await callback.answer()
    if callback.message is None:
        return
    if not await _ensure_family_access(callback.message):
        return

    task_id, page, list_id = parse_task_action_context(
        callback.data,
        TASK_SNOOZE_CUSTOM_CALLBACK_PREFIX,
    )
    if task_id is None:
        await _send_task_list(message=callback.message)
        return

    family_id = _get_message_family_id(callback.message) or DEFAULT_FAMILY_ID
    if task_storage.get_task_by_family(family_id=family_id, task_id=task_id) is None:
        await _send_task_list(
            message=callback.message,
            list_id=list_id or DEFAULT_TASK_LIST_ID,
            page=page or 0,
        )
        return

    await state.update_data(
        selected_snooze_task_id=task_id,
        selected_snooze_list_id=list_id,
        selected_snooze_page=page or 0,
    )
    await state.set_state(SelectedTaskSnoozeStates.waiting_custom_snooze_until)
    await callback.message.answer(text=TASK_SNOOZE_CUSTOM_PROMPT_TEXT)


@router.callback_query(
    F.data.startswith(TASK_RECURRENCE_MENU_CALLBACK_PREFIX),
    F.message.chat.type == "private",
)
async def handle_task_recurrence_menu_callback(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message is None:
        return
    if not await _ensure_family_access(callback.message):
        return

    task_id, page, list_id = parse_task_action_context(
        callback.data,
        TASK_RECURRENCE_MENU_CALLBACK_PREFIX,
    )
    family_id = _get_message_family_id(callback.message) or DEFAULT_FAMILY_ID
    selected_task = task_storage.get_task_by_family(family_id=family_id, task_id=task_id)
    if selected_task is None:
        await _send_task_list(
            message=callback.message,
            list_id=list_id or DEFAULT_TASK_LIST_ID,
            page=page or 0,
        )
        return

    await callback.message.answer(
        text=build_task_list_text([selected_task]),
        reply_markup=build_selected_task_recurrence_keyboard(
            task=selected_task,
            list_id=list_id or selected_task.list_id,
            page=page or 0,
        ),
    )


async def _handle_task_recurrence_update(
    callback: CallbackQuery,
    prefix: str,
    recurrence: Optional[str],
) -> None:
    await callback.answer()
    if callback.message is None:
        return
    if not await _ensure_family_access(callback.message):
        return

    task_id, page, list_id = parse_task_action_context(callback.data, prefix)
    if task_id is None:
        await _send_task_list(message=callback.message)
        return

    family_id = _get_message_family_id(callback.message) or DEFAULT_FAMILY_ID
    selected_task = task_storage.get_task_by_family(family_id=family_id, task_id=task_id)
    if selected_task is None:
        await _send_task_list(
            message=callback.message,
            list_id=list_id or DEFAULT_TASK_LIST_ID,
            page=page or 0,
        )
        return

    if recurrence is not None and selected_task.deadline is None:
        await callback.message.answer(text=TASK_RECURRENCE_NEEDS_DEADLINE_TEXT)
        await _send_selected_task(
            message=callback.message,
            task_id=selected_task.id,
            list_id=list_id or selected_task.list_id,
            page=page or 0,
        )
        return

    updated_task = task_storage.update_task_recurrence_by_family(
        family_id=family_id,
        task_id=selected_task.id,
        recurrence=recurrence,
    )
    if updated_task is None:
        await _send_task_list(
            message=callback.message,
            list_id=list_id or selected_task.list_id,
            page=page or 0,
        )
        return

    if recurrence is None:
        await callback.message.answer(text=TASK_RECURRENCE_REMOVED_TEXT)
    else:
        await callback.message.answer(
            text=TASK_RECURRENCE_UPDATED_TEMPLATE.format(
                recurrence_label=get_recurrence_label(recurrence)
            )
        )

    await _send_selected_task(
        message=callback.message,
        task_id=updated_task.id,
        list_id=list_id or updated_task.list_id,
        page=page or 0,
    )


@router.callback_query(
    F.data.startswith(TASK_RECURRENCE_DAILY_CALLBACK_PREFIX),
    F.message.chat.type == "private",
)
async def handle_task_recurrence_daily_callback(callback: CallbackQuery) -> None:
    await _handle_task_recurrence_update(
        callback=callback,
        prefix=TASK_RECURRENCE_DAILY_CALLBACK_PREFIX,
        recurrence=RECURRENCE_DAILY,
    )


@router.callback_query(
    F.data.startswith(TASK_RECURRENCE_WEEKLY_CALLBACK_PREFIX),
    F.message.chat.type == "private",
)
async def handle_task_recurrence_weekly_callback(callback: CallbackQuery) -> None:
    await _handle_task_recurrence_update(
        callback=callback,
        prefix=TASK_RECURRENCE_WEEKLY_CALLBACK_PREFIX,
        recurrence=RECURRENCE_WEEKLY,
    )


@router.callback_query(
    F.data.startswith(TASK_RECURRENCE_MONTHLY_CALLBACK_PREFIX),
    F.message.chat.type == "private",
)
async def handle_task_recurrence_monthly_callback(callback: CallbackQuery) -> None:
    await _handle_task_recurrence_update(
        callback=callback,
        prefix=TASK_RECURRENCE_MONTHLY_CALLBACK_PREFIX,
        recurrence=RECURRENCE_MONTHLY,
    )


@router.callback_query(
    F.data.startswith(TASK_RECURRENCE_REMOVE_CALLBACK_PREFIX),
    F.message.chat.type == "private",
)
async def handle_task_recurrence_remove_callback(callback: CallbackQuery) -> None:
    await _handle_task_recurrence_update(
        callback=callback,
        prefix=TASK_RECURRENCE_REMOVE_CALLBACK_PREFIX,
        recurrence=None,
    )


@router.callback_query(
    F.data.startswith(TASK_CHANGE_LIST_CALLBACK_PREFIX),
    F.message.chat.type == "private",
)
async def handle_task_change_list_callback(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message is None:
        return
    if not await _ensure_family_access(callback.message):
        return

    task_id, page, list_id = parse_task_action_context(
        callback.data,
        TASK_CHANGE_LIST_CALLBACK_PREFIX,
    )
    if task_id is None:
        await _send_task_list(message=callback.message)
        return

    family_id = _get_message_family_id(callback.message) or DEFAULT_FAMILY_ID
    selected_task = task_storage.get_task_by_family(family_id=family_id, task_id=task_id)
    if selected_task is None:
        await _send_task_list(
            message=callback.message,
            list_id=list_id or DEFAULT_TASK_LIST_ID,
            page=page or 0,
        )
        return

    source_list_id = list_id or selected_task.list_id
    task_lists = task_list_storage.list_task_lists_by_family(family_id=family_id)
    target_lists = [task_list for task_list in task_lists if task_list.id != source_list_id]
    if not target_lists:
        await callback.message.answer(text=CHANGE_TASK_LIST_EMPTY_TEXT)
        await _send_selected_task(
            message=callback.message,
            task_id=selected_task.id,
            list_id=source_list_id,
            page=page or 0,
        )
        return

    await callback.message.answer(
        text=CHANGE_TASK_LIST_TEXT,
        reply_markup=build_change_task_list_keyboard(
            task_id=selected_task.id,
            source_list_id=source_list_id,
            page=page or 0,
            task_lists=task_lists,
        ),
    )


@router.callback_query(
    F.data.startswith(TASK_MOVE_TO_LIST_CALLBACK_PREFIX),
    F.message.chat.type == "private",
)
async def handle_task_move_to_list_callback(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message is None:
        return
    if not await _ensure_family_access(callback.message):
        return

    task_id, _page, source_list_id, target_list_id = parse_task_move_to_list_callback(
        callback.data
    )
    family_id = _get_message_family_id(callback.message) or DEFAULT_FAMILY_ID
    if task_id is None or target_list_id is None:
        await _send_task_list(
            message=callback.message,
            list_id=source_list_id or DEFAULT_TASK_LIST_ID,
        )
        return

    target_list = task_list_storage.get_task_list(
        family_id=family_id,
        list_id=target_list_id,
    )
    if target_list is None:
        await _send_task_list(
            message=callback.message,
            list_id=source_list_id or DEFAULT_TASK_LIST_ID,
        )
        return

    updated_task = task_storage.update_task_list_by_family(
        family_id=family_id,
        task_id=task_id,
        list_id=target_list.id,
    )
    if updated_task is None:
        await _send_task_list(
            message=callback.message,
            list_id=source_list_id or DEFAULT_TASK_LIST_ID,
        )
        return

    await callback.message.answer(
        text=TASK_LIST_CHANGED_TEMPLATE.format(title=target_list.title)
    )
    await _send_task_list(message=callback.message, list_id=target_list.id)


@router.callback_query(
    F.data.startswith(TASK_DEADLINE_TODAY_CALLBACK_PREFIX),
    F.message.chat.type == "private",
)
async def handle_task_deadline_today_callback(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    await callback.answer()
    if callback.message is None:
        return
    if not await _ensure_family_access(callback.message):
        return

    task_id, page, list_id = parse_task_action_context(
        callback.data,
        TASK_DEADLINE_TODAY_CALLBACK_PREFIX,
    )
    if task_id is None:
        await _send_task_list(message=callback.message)
        return

    await _ask_selected_task_deadline_time(
        message=callback.message,
        state=state,
        task_id=task_id,
        deadline=get_today_moscow(),
        list_id=list_id,
        page=page or 0,
    )


@router.callback_query(
    F.data.startswith(TASK_DEADLINE_TOMORROW_CALLBACK_PREFIX),
    F.message.chat.type == "private",
)
async def handle_task_deadline_tomorrow_callback(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    await callback.answer()
    if callback.message is None:
        return
    if not await _ensure_family_access(callback.message):
        return

    task_id, page, list_id = parse_task_action_context(
        callback.data,
        TASK_DEADLINE_TOMORROW_CALLBACK_PREFIX,
    )
    if task_id is None:
        await _send_task_list(message=callback.message)
        return

    await _ask_selected_task_deadline_time(
        message=callback.message,
        state=state,
        task_id=task_id,
        deadline=get_tomorrow_moscow(),
        list_id=list_id,
        page=page or 0,
    )


@router.callback_query(
    F.data.startswith(TASK_DEADLINE_CUSTOM_CALLBACK_PREFIX),
    F.message.chat.type == "private",
)
async def handle_task_deadline_custom_callback(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    await callback.answer()
    if callback.message is None:
        return
    if not await _ensure_family_access(callback.message):
        return

    task_id, page, list_id = parse_task_action_context(
        callback.data,
        TASK_DEADLINE_CUSTOM_CALLBACK_PREFIX,
    )
    if task_id is None:
        await _send_task_list(message=callback.message)
        return

    family_id = _get_message_family_id(callback.message) or DEFAULT_FAMILY_ID
    if task_storage.get_task_by_family(family_id=family_id, task_id=task_id) is None:
        await _send_task_list(
            message=callback.message,
            list_id=list_id or DEFAULT_TASK_LIST_ID,
            page=page or 0,
        )
        return

    await state.update_data(
        selected_deadline_task_id=task_id,
        selected_deadline_list_id=list_id,
        selected_deadline_page=page or 0,
    )
    await state.set_state(SelectedTaskDeadlineStates.waiting_custom_deadline)
    await callback.message.answer(text=CUSTOM_DEADLINE_PROMPT_TEXT)


@router.callback_query(
    F.data.startswith(TASK_DEADLINE_REMOVE_CALLBACK_PREFIX),
    F.message.chat.type == "private",
)
async def handle_task_deadline_remove_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if callback.message is None:
        return
    if not await _ensure_family_access(callback.message):
        return

    task_id, page, list_id = parse_task_action_context(
        callback.data,
        TASK_DEADLINE_REMOVE_CALLBACK_PREFIX,
    )
    if task_id is None:
        await _send_task_list(message=callback.message)
        return

    await state.clear()
    updated = task_storage.update_task_deadline_by_family(
        family_id=_get_message_family_id(callback.message) or DEFAULT_FAMILY_ID,
        task_id=task_id,
        deadline=None,
    )
    if not updated:
        await _send_task_list(message=callback.message)
        return

    await callback.message.answer(text=DEADLINE_SKIPPED_TEXT)
    wake_reminder_scheduler("task_deadline_removed")
    await _notify_deadline_updated(message=callback.message, task=updated)
    await _send_selected_task(
        message=callback.message,
        task_id=task_id,
        list_id=list_id,
        page=page or 0,
    )


@router.callback_query(
    SelectedTaskDeadlineStates.waiting_deadline_time,
    F.data == DEADLINE_TIME_SKIP_CALLBACK,
    F.message.chat.type == "private",
)
async def handle_selected_task_deadline_time_skip(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    await callback.answer()
    if callback.message is None:
        return
    if not await _ensure_family_access(callback.message):
        await state.clear()
        return

    data = await state.get_data()
    task_id = _get_selected_deadline_task_id(data)
    pending_deadline = _get_pending_deadline(data)
    list_id = _get_selected_deadline_list_id(data)
    page = _get_selected_deadline_page(data)
    await state.clear()
    if task_id is None or pending_deadline is None:
        await _send_task_list(
            message=callback.message,
            list_id=list_id or DEFAULT_TASK_LIST_ID,
            page=page,
        )
        return

    updated = task_storage.update_task_deadline_by_family(
        family_id=_get_message_family_id(callback.message) or DEFAULT_FAMILY_ID,
        task_id=task_id,
        deadline=pending_deadline,
    )
    if updated is None:
        await _send_task_list(
            message=callback.message,
            list_id=list_id or DEFAULT_TASK_LIST_ID,
            page=page,
        )
        return

    await callback.message.answer(text=DEADLINE_ADDED_TEXT)
    wake_reminder_scheduler("task_deadline_updated")
    await _notify_deadline_updated(message=callback.message, task=updated)
    await _send_selected_task(
        message=callback.message,
        task_id=task_id,
        list_id=list_id,
        page=page,
    )


@router.callback_query(F.data.startswith(TASK_DONE_CALLBACK_PREFIX), F.message.chat.type == "private")
async def handle_task_done_callback(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message is None:
        return
    if not await _ensure_family_access(callback.message):
        return

    task_id, page, list_id = parse_task_action_context(
        callback.data,
        TASK_DONE_CALLBACK_PREFIX,
    )
    completed_task, changed = (
        task_storage.complete_task_once_by_family(
            family_id=_get_message_family_id(callback.message) or DEFAULT_FAMILY_ID,
            task_id=task_id,
        )
        if task_id is not None
        else (None, False)
    )
    if completed_task is not None and changed:
        next_recurring_task = _create_next_recurring_task(completed_task)
        wake_reminder_scheduler("task_done")
        await callback.message.answer(text=TASK_DONE_TEXT)
        if next_recurring_task is not None and next_recurring_task.deadline is not None:
            await callback.message.answer(
                text=TASK_RECURRING_NEXT_TEMPLATE.format(
                    deadline=format_deadline_for_user(
                        next_recurring_task.deadline,
                        next_recurring_task.deadline_time,
                    )
                )
            )
        author_name = _get_family_member_display_name(callback.message.chat.id)
        await _notify_task_action(
            message=callback.message,
            actor_chat_id=callback.message.chat.id,
            text=build_task_done_notification(author_name, completed_task),
        )

    await _send_task_list(
        message=callback.message,
        list_id=(
            list_id
            or (completed_task.list_id if completed_task is not None else DEFAULT_TASK_LIST_ID)
        ),
        page=page or 0,
    )


@router.callback_query(
    (F.data == TASK_BACK_CALLBACK_DATA) | F.data.startswith(TASK_BACK_CALLBACK_PREFIX),
    F.message.chat.type == "private",
)
async def handle_task_back_callback(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message is None:
        return
    if not await _ensure_family_access(callback.message):
        return

    list_id, page = parse_task_back_context(callback.data)
    await _send_task_list(
        message=callback.message,
        list_id=list_id or DEFAULT_TASK_LIST_ID,
        page=page,
    )


@router.callback_query(
    F.data.startswith(TASK_SNOOZED_BACK_CALLBACK_PREFIX),
    F.message.chat.type == "private",
)
async def handle_task_snoozed_back_callback(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message is None:
        return
    if not await _ensure_family_access(callback.message):
        return

    list_id, page = parse_task_snoozed_back_context(callback.data)
    await _send_snoozed_task_list(
        message=callback.message,
        list_id=list_id or DEFAULT_TASK_LIST_ID,
        page=page,
    )
