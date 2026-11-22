"""Daily due-task reminder scheduling."""

from __future__ import annotations

import asyncio
import logging
from contextlib import suppress
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Awaitable, Callable, Mapping, Optional, Sequence

from aiogram import Bot

from easy_task_manager.config import (
    get_families_file_path,
    get_task_lists_file_path,
)
from easy_task_manager.deadline_utils import MOSCOW_TIMEZONE, get_today_moscow
from easy_task_manager.family_storage import JsonFamilyStorage
from easy_task_manager.keyboards import build_start_keyboard
from easy_task_manager.reminder_contract import (
    build_exact_deadline_reminder_text,
    build_evening_reminder_text,
    build_morning_reminder_text,
)
from easy_task_manager.reminder_state_storage import JsonReminderStateStorage
from easy_task_manager.task_list_storage import JsonTaskListStorage
from easy_task_manager.task_storage import JsonTaskStorage, Task

logger = logging.getLogger(__name__)
family_storage = JsonFamilyStorage(file_path=get_families_file_path())
task_list_storage = JsonTaskListStorage(file_path=get_task_lists_file_path())


ReminderTextBuilder = Callable[[Sequence[Task], Optional[Mapping[str, str]]], str]
SleepFunc = Callable[[float], Awaitable[None]]
NowProvider = Callable[[], datetime]


@dataclass(frozen=True)
class ReminderSlot:
    """Daily reminder slot in Moscow time."""

    name: str
    at: time
    build_text: ReminderTextBuilder


REMINDER_SLOTS = (
    ReminderSlot(
        name="morning",
        at=time(hour=9, minute=0),
        build_text=build_morning_reminder_text,
    ),
    ReminderSlot(
        name="evening",
        at=time(hour=18, minute=0),
        build_text=build_evening_reminder_text,
    ),
)


def _now_moscow() -> datetime:
    return datetime.now(tz=MOSCOW_TIMEZONE)


async def send_due_task_reminders(
    bot: Bot,
    storage: JsonTaskStorage,
    slot: ReminderSlot,
) -> int:
    """Send due-task reminders for a single reminder slot."""
    due_tasks_by_family = storage.list_due_tasks_by_family(today=get_today_moscow())
    sent_count = 0

    for family_id, tasks in due_tasks_by_family.items():
        text = slot.build_text(tasks, _get_task_list_titles(family_id=family_id))
        if not text:
            continue

        recipient_chat_ids = family_storage.list_family_chat_ids(family_id=family_id)

        for chat_id in recipient_chat_ids:
            try:
                await bot.send_message(chat_id=chat_id, text=text)
            except Exception:
                logger.exception(
                    "due_task_reminder_failed slot=%s family_id=%s chat_id=%s",
                    slot.name,
                    family_id,
                    chat_id,
                )
                continue

            sent_count += 1
            logger.info(
                "due_task_reminder_sent slot=%s family_id=%s chat_id=%s task_count=%s",
                slot.name,
                family_id,
                chat_id,
                len(tasks),
            )

    return sent_count


async def send_timed_due_task_reminders(
    bot: Bot,
    storage: JsonTaskStorage,
    now: datetime,
) -> int:
    """Send exact deadline reminders for timed tasks."""
    local_now = now.astimezone(MOSCOW_TIMEZONE)
    due_tasks_by_family = storage.list_timed_due_tasks_by_family(now=local_now)
    sent_count = 0

    for family_id, tasks in due_tasks_by_family.items():
        text = build_exact_deadline_reminder_text(
            tasks,
            list_titles=_get_task_list_titles(family_id=family_id),
        )
        if not text:
            continue

        family_sent_count = 0
        recipient_chat_ids = family_storage.list_family_chat_ids(family_id=family_id)

        for chat_id in recipient_chat_ids:
            try:
                await bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=build_start_keyboard(),
                )
            except Exception:
                logger.exception(
                    "timed_due_task_reminder_failed family_id=%s chat_id=%s",
                    family_id,
                    chat_id,
                )
                continue
            family_sent_count += 1

        if family_sent_count:
            storage.mark_family_deadline_notifications_sent(
                family_id=family_id,
                task_ids=[task.id for task in tasks],
                notified_at=local_now,
            )
            sent_count += family_sent_count
            logger.info(
                "timed_due_task_reminder_sent family_id=%s recipient_count=%s task_count=%s",
                family_id,
                family_sent_count,
                len(tasks),
            )

    return sent_count


def _get_task_list_titles(family_id: str) -> dict[str, str]:
    return {
        task_list.id: task_list.title
        for task_list in task_list_storage.list_task_lists_by_family(family_id=family_id)
    }


async def run_due_task_reminder_scheduler(
    bot: Bot,
    storage: JsonTaskStorage,
    reminder_state: JsonReminderStateStorage,
    sleep: SleepFunc = asyncio.sleep,
    now_provider: NowProvider = _now_moscow,
    wakeup_event: asyncio.Event | None = None,
) -> None:
    """Run due-task reminders forever."""
    while True:
        now = now_provider().astimezone(MOSCOW_TIMEZONE)
        planned_at, slot = _get_next_scheduler_run(
            now=now,
            storage=storage,
            reminder_state=reminder_state,
        )
        wait_seconds = max(0.0, (planned_at - now).total_seconds())
        logger.info(
            "due_task_reminder_scheduled slot=%s planned_at=%s wait_seconds=%.0f",
            slot.name if slot is not None else "exact_deadline",
            planned_at.isoformat(),
            wait_seconds,
        )
        was_woken = await _wait_for_scheduler_trigger(
            wait_seconds=wait_seconds,
            sleep=sleep,
            wakeup_event=wakeup_event,
        )
        if was_woken:
            logger.info("due_task_reminder_rescheduled_after_wakeup")
            continue

        if slot is None:
            await send_timed_due_task_reminders(
                bot=bot,
                storage=storage,
                now=planned_at,
            )
        else:
            await send_due_task_reminders(bot=bot, storage=storage, slot=slot)
            _mark_daily_slots_processed_through(
                reminder_state=reminder_state,
                day=planned_at.date(),
                slot=slot,
                processed_at=planned_at,
            )


async def _wait_for_scheduler_trigger(
    wait_seconds: float,
    sleep: SleepFunc,
    wakeup_event: asyncio.Event | None,
) -> bool:
    if wakeup_event is None:
        await sleep(wait_seconds)
        return False

    if wakeup_event.is_set():
        wakeup_event.clear()
        return True

    sleep_task = asyncio.create_task(sleep(wait_seconds))
    wakeup_task = asyncio.create_task(wakeup_event.wait())
    done, pending = await asyncio.wait(
        {sleep_task, wakeup_task},
        return_when=asyncio.FIRST_COMPLETED,
    )

    for task in pending:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task

    if wakeup_task in done or wakeup_event.is_set():
        wakeup_event.clear()
        return True

    await sleep_task
    return False


def _get_next_scheduler_run(
    now: datetime,
    storage: JsonTaskStorage,
    reminder_state: JsonReminderStateStorage | None = None,
) -> tuple[datetime, ReminderSlot | None]:
    local_now = now.astimezone(MOSCOW_TIMEZONE)
    if storage.list_timed_due_tasks_by_family(now=local_now):
        return local_now, None

    if reminder_state is not None:
        missed_slot = _get_latest_unprocessed_reached_reminder_slot(
            now=local_now,
            reminder_state=reminder_state,
        )
        if missed_slot is not None:
            return local_now, missed_slot

    next_daily_at, slot = _get_next_reminder_run(local_now)
    next_timed_at = storage.get_next_timed_deadline_at(now=local_now)
    if next_timed_at is not None and next_timed_at < next_daily_at:
        return next_timed_at, None
    return next_daily_at, slot


def _get_next_reminder_run(now: datetime) -> tuple[datetime, ReminderSlot]:
    local_now = now.astimezone(MOSCOW_TIMEZONE)
    for slot in REMINDER_SLOTS:
        candidate = datetime.combine(
            local_now.date(),
            slot.at,
            tzinfo=MOSCOW_TIMEZONE,
        )
        if candidate > local_now:
            return candidate, slot

    first_slot = REMINDER_SLOTS[0]
    tomorrow = local_now.date() + timedelta(days=1)
    return (
        datetime.combine(tomorrow, first_slot.at, tzinfo=MOSCOW_TIMEZONE),
        first_slot,
    )


def _get_latest_unprocessed_reached_reminder_slot(
    now: datetime,
    reminder_state: JsonReminderStateStorage,
) -> ReminderSlot | None:
    local_now = now.astimezone(MOSCOW_TIMEZONE)
    reached_slots = []
    for slot in REMINDER_SLOTS:
        candidate = datetime.combine(
            local_now.date(),
            slot.at,
            tzinfo=MOSCOW_TIMEZONE,
        )
        if candidate > local_now:
            continue
        if reminder_state.is_daily_slot_processed(local_now.date(), slot.name):
            continue
        reached_slots.append(slot)

    if not reached_slots:
        return None
    return reached_slots[-1]


def _mark_daily_slots_processed_through(
    reminder_state: JsonReminderStateStorage,
    day: date,
    slot: ReminderSlot,
    processed_at: datetime,
) -> None:
    for reminder_slot in REMINDER_SLOTS:
        if reminder_slot.at > slot.at:
            continue
        reminder_state.mark_daily_slot_processed(
            day=day,
            slot_name=reminder_slot.name,
            processed_at=processed_at,
        )
