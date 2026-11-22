"""Handlers for add-task flow."""

from __future__ import annotations

from datetime import date, time
from typing import Optional

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from easy_task_manager.action_notifications import (
    build_task_created_notification,
    send_family_action_notification,
)
from easy_task_manager.add_task_contract import (
    ASK_DEADLINE_TEXT,
    ASK_DEADLINE_TIME_TEXT,
    ASK_RECURRENCE_TEXT,
    ASK_TASK_TEXT,
    CUSTOM_DEADLINE_INVALID_TEXT,
    CUSTOM_DEADLINE_TIME_INVALID_TEXT,
    CUSTOM_DEADLINE_PROMPT_TEXT,
    DEADLINE_ADDED_TEXT,
    DEADLINE_CUSTOM_CALLBACK,
    DEADLINE_SKIPPED_TEXT,
    DEADLINE_SKIP_CALLBACK,
    DEADLINE_TIME_ADDED_TEXT,
    DEADLINE_TIME_SKIP_CALLBACK,
    DEADLINE_TODAY_CALLBACK,
    DEADLINE_TOMORROW_CALLBACK,
    RECURRENCE_ADDED_TEMPLATE,
    RECURRENCE_DAILY_CALLBACK,
    RECURRENCE_MONTHLY_CALLBACK,
    RECURRENCE_SKIP_CALLBACK,
    RECURRENCE_SKIPPED_TEXT,
    RECURRENCE_WEEKLY_CALLBACK,
    TASK_ADDED_TEMPLATE,
)
from easy_task_manager.config import (
    get_families_file_path,
    get_family_member_name,
    get_task_lists_file_path,
    get_tasks_file_path,
)
from easy_task_manager.deadline_utils import (
    get_today_moscow,
    get_tomorrow_moscow,
    is_past_deadline,
    is_past_deadline_time,
    parse_custom_deadline,
    parse_deadline_time,
)
from easy_task_manager.handlers.start import send_start_message
from easy_task_manager.family_storage import JsonFamilyStorage
from easy_task_manager.keyboards import (
    build_add_task_list_choice_keyboard,
    build_deadline_keyboard,
    build_deadline_time_keyboard,
    build_recurrence_keyboard,
)
from easy_task_manager.recurrence import (
    RECURRENCE_DAILY,
    RECURRENCE_MONTHLY,
    RECURRENCE_WEEKLY,
    get_recurrence_label,
)
from easy_task_manager.reminder_wakeup import wake_reminder_scheduler
from easy_task_manager.start_contract import (
    ADD_TASK_CALLBACK_DATA,
    UNKNOWN_USER_TEXT,
    is_cancel_message,
)
from easy_task_manager.task_storage import DEFAULT_FAMILY_ID, JsonTaskStorage
from easy_task_manager.task_list_storage import (
    DEFAULT_TASK_LIST_ID,
    JsonTaskListStorage,
)
from easy_task_manager.task_lists_contract import (
    ADD_TASK_TO_LIST_CALLBACK_PREFIX,
    ASK_TASK_LIST_TEXT,
    parse_callback_suffix,
)

router = Router(name="add-task-router")
task_storage = JsonTaskStorage(file_path=get_tasks_file_path())
task_list_storage = JsonTaskListStorage(file_path=get_task_lists_file_path())
family_storage = JsonFamilyStorage(file_path=get_families_file_path())


class AddTaskStates(StatesGroup):
    waiting_task_list_choice = State()
    waiting_task_text = State()
    waiting_deadline_choice = State()
    waiting_custom_deadline = State()
    waiting_deadline_time = State()
    waiting_recurrence_choice = State()


async def _send_unknown_user_message(message: Message) -> None:
    await message.answer(text=UNKNOWN_USER_TEXT)


async def _ensure_family_access(message: Message) -> bool:
    if _get_family_id_for_chat(message.chat.id) is not None:
        return True
    await _send_unknown_user_message(message)
    return False


def _get_family_id_for_chat(chat_id: int) -> Optional[str]:
    return family_storage.get_family_id_for_chat(chat_id=chat_id)


def _get_family_member_display_name(chat_id: int) -> str:
    if family_storage.get_member(chat_id=chat_id) is not None:
        return family_storage.get_member_name(chat_id=chat_id)
    return get_family_member_name(chat_id)


def _get_selected_task_list_id(data: dict[str, object]) -> str:
    raw_list_id = str(data.get("selected_task_list_id") or "").strip()
    return raw_list_id or DEFAULT_TASK_LIST_ID


async def _complete_task_creation(
    message: Message,
    state: FSMContext,
    task_text: str,
    deadline: Optional[date],
    deadline_time: Optional[time] = None,
    recurrence: Optional[str] = None,
) -> None:
    family_id = _get_family_id_for_chat(message.chat.id)
    if family_id is None:
        await _send_unknown_user_message(message)
        await state.clear()
        return

    data = await state.get_data()
    list_id = _get_selected_task_list_id(data)
    if task_list_storage.get_task_list(family_id=family_id, list_id=list_id) is None:
        list_id = task_list_storage.ensure_default_task_list(family_id=family_id).id

    task = task_storage.add_task(
        chat_id=message.chat.id,
        text=task_text,
        deadline=deadline,
        deadline_time=deadline_time,
        family_id=family_id,
        list_id=list_id,
        recurrence=recurrence,
    )
    wake_reminder_scheduler("task_created")
    await state.clear()
    await send_start_message(message=message, source="add_task_complete")
    bot = getattr(message, "bot", None)
    if bot is not None:
        author_name = _get_family_member_display_name(message.chat.id)
        await send_family_action_notification(
            bot=bot,
            actor_chat_id=message.chat.id,
            family_id=family_id,
            text=build_task_created_notification(author_name, task),
        )


async def _ask_deadline_time(message: Message, state: FSMContext, deadline: date) -> None:
    await state.update_data(pending_deadline=deadline.isoformat())
    await state.set_state(AddTaskStates.waiting_deadline_time)
    await message.answer(
        text=ASK_DEADLINE_TIME_TEXT,
        reply_markup=build_deadline_time_keyboard(),
    )


async def _ask_recurrence(
    message: Message,
    state: FSMContext,
    deadline: date,
    deadline_time: Optional[time] = None,
) -> None:
    await state.update_data(
        pending_deadline=deadline.isoformat(),
        pending_deadline_time=deadline_time.strftime("%H:%M") if deadline_time else None,
    )
    await state.set_state(AddTaskStates.waiting_recurrence_choice)
    await message.answer(
        text=ASK_RECURRENCE_TEXT,
        reply_markup=build_recurrence_keyboard(),
    )


def _get_pending_deadline(data: dict[str, object]) -> Optional[date]:
    raw_deadline = data.get("pending_deadline")
    if not raw_deadline:
        return None
    try:
        return date.fromisoformat(str(raw_deadline))
    except ValueError:
        return None


def _get_pending_deadline_time(data: dict[str, object]) -> Optional[time]:
    raw_deadline_time = data.get("pending_deadline_time")
    if not raw_deadline_time:
        return None
    try:
        return time.fromisoformat(str(raw_deadline_time))
    except ValueError:
        return None


async def _cancel_to_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await send_start_message(message=message, source="cancel_text")


@router.callback_query(F.data == ADD_TASK_CALLBACK_DATA, F.message.chat.type == "private")
async def handle_add_button(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    if callback.message is None:
        return
    await _start_add_task_flow(message=callback.message, state=state)


@router.message(Command("add"), F.chat.type == "private")
async def handle_add_command(message: Message, state: FSMContext) -> None:
    await state.clear()
    await _start_add_task_flow(message=message, state=state)


async def _start_add_task_flow(message: Message, state: FSMContext) -> None:
    if not await _ensure_family_access(message):
        await state.clear()
        return
    family_id = _get_family_id_for_chat(message.chat.id) or DEFAULT_FAMILY_ID
    task_lists = task_list_storage.list_task_lists_by_family(family_id=family_id)
    if len(task_lists) > 1:
        await state.set_state(AddTaskStates.waiting_task_list_choice)
        await message.answer(
            text=ASK_TASK_LIST_TEXT,
            reply_markup=build_add_task_list_choice_keyboard(task_lists=task_lists),
        )
        return

    selected_list = task_lists[0] if task_lists else task_list_storage.ensure_default_task_list(family_id)
    await state.update_data(selected_task_list_id=selected_list.id)
    await state.set_state(AddTaskStates.waiting_task_text)
    await message.answer(text=ASK_TASK_TEXT)


@router.callback_query(
    F.data.startswith(ADD_TASK_TO_LIST_CALLBACK_PREFIX),
    F.message.chat.type == "private",
)
async def handle_add_to_list_button(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    if callback.message is None:
        return
    if not await _ensure_family_access(callback.message):
        await state.clear()
        return

    family_id = _get_family_id_for_chat(callback.message.chat.id) or DEFAULT_FAMILY_ID
    list_id = parse_callback_suffix(callback.data, ADD_TASK_TO_LIST_CALLBACK_PREFIX)
    task_list = (
        task_list_storage.get_task_list(family_id=family_id, list_id=list_id)
        if list_id is not None
        else None
    )
    if task_list is None:
        task_list = task_list_storage.ensure_default_task_list(family_id=family_id)

    await state.update_data(selected_task_list_id=task_list.id)
    await state.set_state(AddTaskStates.waiting_task_text)
    await callback.message.answer(text=ASK_TASK_TEXT)


@router.message(AddTaskStates.waiting_task_text, F.chat.type == "private", F.text)
async def handle_task_text(message: Message, state: FSMContext) -> None:
    if not await _ensure_family_access(message):
        await state.clear()
        return

    if is_cancel_message(message.text):
        await _cancel_to_start(message=message, state=state)
        return

    task_text = message.text.strip()
    if not task_text:
        await message.answer(text=ASK_TASK_TEXT)
        return
    await state.update_data(task_text=task_text)
    await state.set_state(AddTaskStates.waiting_deadline_choice)
    await message.answer(text=TASK_ADDED_TEMPLATE.format(task_text=task_text))
    await message.answer(text=ASK_DEADLINE_TEXT, reply_markup=build_deadline_keyboard())


@router.callback_query(
    AddTaskStates.waiting_deadline_choice,
    F.data.in_(
        {
            DEADLINE_TODAY_CALLBACK,
            DEADLINE_TOMORROW_CALLBACK,
            DEADLINE_SKIP_CALLBACK,
            DEADLINE_CUSTOM_CALLBACK,
        }
    ),
)
async def handle_deadline_choice(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if callback.message is None:
        return
    if not await _ensure_family_access(callback.message):
        await state.clear()
        return

    if callback.data == DEADLINE_CUSTOM_CALLBACK:
        await state.set_state(AddTaskStates.waiting_custom_deadline)
        await callback.message.answer(text=CUSTOM_DEADLINE_PROMPT_TEXT)
        return

    data = await state.get_data()
    task_text = str(data.get("task_text", "")).strip()
    if not task_text:
        await state.clear()
        await send_start_message(message=callback.message, source="add_task_reset")
        return

    if callback.data == DEADLINE_TODAY_CALLBACK:
        await _ask_deadline_time(
            message=callback.message,
            state=state,
            deadline=get_today_moscow(),
        )
        return

    if callback.data == DEADLINE_TOMORROW_CALLBACK:
        await _ask_deadline_time(
            message=callback.message,
            state=state,
            deadline=get_tomorrow_moscow(),
        )
        return

    await callback.message.answer(text=DEADLINE_SKIPPED_TEXT)
    await _complete_task_creation(
        message=callback.message,
        state=state,
        task_text=task_text,
        deadline=None,
    )


@router.message(AddTaskStates.waiting_custom_deadline, F.chat.type == "private", F.text)
async def handle_custom_deadline(message: Message, state: FSMContext) -> None:
    if not await _ensure_family_access(message):
        await state.clear()
        return

    if is_cancel_message(message.text):
        await _cancel_to_start(message=message, state=state)
        return

    data = await state.get_data()
    task_text = str(data.get("task_text", "")).strip()
    if not task_text:
        await state.clear()
        await send_start_message(message=message, source="custom_deadline_reset")
        return

    try:
        parsed_date = parse_custom_deadline(message.text)
    except ValueError:
        await message.answer(text=CUSTOM_DEADLINE_INVALID_TEXT)
        return

    if is_past_deadline(parsed_date):
        await message.answer(text=CUSTOM_DEADLINE_INVALID_TEXT)
        return

    await _ask_deadline_time(message=message, state=state, deadline=parsed_date)


@router.callback_query(
    AddTaskStates.waiting_deadline_time,
    F.data == DEADLINE_TIME_SKIP_CALLBACK,
    F.message.chat.type == "private",
)
async def handle_deadline_time_skip(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if callback.message is None:
        return
    if not await _ensure_family_access(callback.message):
        await state.clear()
        return

    data = await state.get_data()
    task_text = str(data.get("task_text", "")).strip()
    pending_deadline = _get_pending_deadline(data)
    if not task_text or pending_deadline is None:
        await state.clear()
        await send_start_message(message=callback.message, source="deadline_time_reset")
        return

    await callback.message.answer(text=DEADLINE_ADDED_TEXT)
    await _ask_recurrence(
        message=callback.message,
        state=state,
        deadline=pending_deadline,
    )


@router.message(AddTaskStates.waiting_deadline_time, F.chat.type == "private", F.text)
async def handle_deadline_time(message: Message, state: FSMContext) -> None:
    if not await _ensure_family_access(message):
        await state.clear()
        return

    if is_cancel_message(message.text):
        await _cancel_to_start(message=message, state=state)
        return

    data = await state.get_data()
    task_text = str(data.get("task_text", "")).strip()
    pending_deadline = _get_pending_deadline(data)
    if not task_text or pending_deadline is None:
        await state.clear()
        await send_start_message(message=message, source="deadline_time_reset")
        return

    try:
        parsed_time = parse_deadline_time(message.text)
    except ValueError:
        await message.answer(text=CUSTOM_DEADLINE_TIME_INVALID_TEXT)
        return

    if is_past_deadline_time(pending_deadline, parsed_time):
        await message.answer(text=CUSTOM_DEADLINE_TIME_INVALID_TEXT)
        return

    await message.answer(text=DEADLINE_TIME_ADDED_TEXT)
    await _ask_recurrence(
        message=message,
        state=state,
        deadline=pending_deadline,
        deadline_time=parsed_time,
    )


@router.callback_query(
    AddTaskStates.waiting_recurrence_choice,
    F.data.in_(
        {
            RECURRENCE_DAILY_CALLBACK,
            RECURRENCE_WEEKLY_CALLBACK,
            RECURRENCE_MONTHLY_CALLBACK,
            RECURRENCE_SKIP_CALLBACK,
        }
    ),
)
async def handle_recurrence_choice(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if callback.message is None:
        return
    if not await _ensure_family_access(callback.message):
        await state.clear()
        return

    data = await state.get_data()
    task_text = str(data.get("task_text", "")).strip()
    pending_deadline = _get_pending_deadline(data)
    pending_deadline_time = _get_pending_deadline_time(data)
    if not task_text or pending_deadline is None:
        await state.clear()
        await send_start_message(message=callback.message, source="recurrence_reset")
        return

    recurrence = None
    if callback.data == RECURRENCE_DAILY_CALLBACK:
        recurrence = RECURRENCE_DAILY
    elif callback.data == RECURRENCE_WEEKLY_CALLBACK:
        recurrence = RECURRENCE_WEEKLY
    elif callback.data == RECURRENCE_MONTHLY_CALLBACK:
        recurrence = RECURRENCE_MONTHLY

    if recurrence is None:
        await callback.message.answer(text=RECURRENCE_SKIPPED_TEXT)
    else:
        await callback.message.answer(
            text=RECURRENCE_ADDED_TEMPLATE.format(
                recurrence_label=get_recurrence_label(recurrence)
            )
        )

    await _complete_task_creation(
        message=callback.message,
        state=state,
        task_text=task_text,
        deadline=pending_deadline,
        deadline_time=pending_deadline_time,
        recurrence=recurrence,
    )
