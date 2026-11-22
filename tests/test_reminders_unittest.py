import asyncio
import json
import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path
from unittest.mock import patch

from easy_task_manager.deadline_utils import MOSCOW_TIMEZONE
from easy_task_manager.reminders import (
    REMINDER_SLOTS,
    _get_next_reminder_run,
    _get_next_scheduler_run,
    run_due_task_reminder_scheduler,
    send_due_task_reminders,
    send_timed_due_task_reminders,
    family_storage,
    task_list_storage,
)
from easy_task_manager.reminder_state_storage import JsonReminderStateStorage
from easy_task_manager.task_storage import JsonTaskStorage


class FakeBot:
    def __init__(self) -> None:
        self.messages: list[tuple[int, str]] = []
        self.reply_markups: list[object] = []

    async def send_message(self, chat_id: int, text: str, reply_markup: object = None) -> None:
        self.messages.append((chat_id, text))
        self.reply_markups.append(reply_markup)


class StopScheduler(Exception):
    pass


class ReminderTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        self.storage_paths = (
            (family_storage, family_storage.file_path),
            (task_list_storage, task_list_storage.file_path),
        )
        family_storage.file_path = root / "families.json"
        task_list_storage.file_path = root / "task_lists.json"
        family_storage.initialize({100: "Паша", 200: "Маша"})
        task_list_storage.initialize()

    def tearDown(self) -> None:
        for storage, path in self.storage_paths:
            storage.file_path = path
        self.temp_dir.cleanup()

    async def test_send_due_task_reminders_sends_messages_to_chats_with_due_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "tasks.json"
            file_path.write_text(
                json.dumps(
                    [
                        {
                            "id": 1,
                            "chat_id": 100,
                            "text": "Просроченная",
                            "deadline": "2026-06-01",
                            "created_at": "2026-06-01T09:00:00+00:00",
                        },
                        {
                            "id": 2,
                            "chat_id": 100,
                            "text": "Сегодня",
                            "deadline": "2026-06-02",
                            "created_at": "2026-06-01T10:00:00+00:00",
                        },
                        {
                            "id": 3,
                            "chat_id": 200,
                            "text": "Завтра",
                            "deadline": "2026-06-03",
                            "created_at": "2026-06-01T11:00:00+00:00",
                        },
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            bot = FakeBot()
            storage = JsonTaskStorage(file_path=file_path)

            with patch("easy_task_manager.reminders.get_today_moscow", return_value=date(2026, 6, 2)):
                sent_count = await send_due_task_reminders(
                    bot=bot,
                    storage=storage,
                    slot=REMINDER_SLOTS[0],
                )

            self.assertEqual(sent_count, 2)
            self.assertEqual(
                bot.messages,
                [
                    (
                        100,
                        "Сегодня тебе надо сделать вот это:\n"
                        "01.06.2026\n"
                        "#1 Просроченная\n\n"
                        "02.06.2026\n"
                        "#2 Сегодня",
                    ),
                    (
                        200,
                        "Сегодня тебе надо сделать вот это:\n"
                        "01.06.2026\n"
                        "#1 Просроченная\n\n"
                        "02.06.2026\n"
                        "#2 Сегодня",
                    ),
                ],
            )

    async def test_send_due_task_reminders_skips_empty_due_list(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "tasks.json"
            file_path.write_text(
                json.dumps(
                    [
                        {
                            "id": 1,
                            "chat_id": 100,
                            "text": "Завтра",
                            "deadline": "2026-06-03",
                            "created_at": "2026-06-01T09:00:00+00:00",
                        }
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            bot = FakeBot()
            storage = JsonTaskStorage(file_path=file_path)

            with patch("easy_task_manager.reminders.get_today_moscow", return_value=date(2026, 6, 2)):
                sent_count = await send_due_task_reminders(
                    bot=bot,
                    storage=storage,
                    slot=REMINDER_SLOTS[1],
                )

            self.assertEqual(sent_count, 0)
            self.assertEqual(bot.messages, [])

    async def test_send_due_task_reminders_uses_recipients_from_each_family(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "tasks.json"
            file_path.write_text(
                json.dumps(
                    [
                        {
                            "id": 1,
                            "family_id": "family_a",
                            "chat_id": 100,
                            "text": "Купить молоко",
                            "deadline": "2026-06-02",
                            "created_at": "2026-06-01T09:00:00+00:00",
                        },
                        {
                            "id": 2,
                            "family_id": "family_b",
                            "chat_id": 300,
                            "text": "Оплатить интернет",
                            "deadline": "2026-06-02",
                            "created_at": "2026-06-01T09:00:00+00:00",
                        },
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            bot = FakeBot()
            storage = JsonTaskStorage(file_path=file_path)

            def recipients(family_id: str) -> tuple[int, ...]:
                return {"family_a": (100, 200), "family_b": (300,)}[family_id]

            with patch(
                "easy_task_manager.reminders.get_today_moscow",
                return_value=date(2026, 6, 2),
            ), patch(
                "easy_task_manager.reminders.family_storage.list_family_chat_ids",
                side_effect=recipients,
            ):
                sent_count = await send_due_task_reminders(
                    bot=bot,
                    storage=storage,
                    slot=REMINDER_SLOTS[0],
                )

            self.assertEqual(sent_count, 3)
            self.assertEqual(
                bot.messages,
                [
                    (
                        100,
                        "Сегодня тебе надо сделать вот это:\n"
                        "02.06.2026\n#1 Купить молоко",
                    ),
                    (
                        200,
                        "Сегодня тебе надо сделать вот это:\n"
                        "02.06.2026\n#1 Купить молоко",
                    ),
                    (
                        300,
                        "Сегодня тебе надо сделать вот это:\n"
                        "02.06.2026\n#2 Оплатить интернет",
                    ),
                ],
            )

    async def test_send_timed_due_task_reminders_sends_and_marks_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "tasks.json"
            file_path.write_text(
                json.dumps(
                    [
                        {
                            "id": 1,
                            "chat_id": 100,
                            "text": "Оплатить интернет",
                            "deadline": "2026-06-02",
                            "deadline_time": "18:30",
                            "deadline_notified_at": None,
                            "created_at": "2026-06-01T09:00:00+00:00",
                        },
                        {
                            "id": 2,
                            "chat_id": 100,
                            "text": "Позже",
                            "deadline": "2026-06-02",
                            "deadline_time": "18:45",
                            "deadline_notified_at": None,
                            "created_at": "2026-06-01T09:00:00+00:00",
                        },
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            bot = FakeBot()
            storage = JsonTaskStorage(file_path=file_path)

            sent_count = await send_timed_due_task_reminders(
                bot=bot,
                storage=storage,
                now=datetime(2026, 6, 2, 18, 30, tzinfo=MOSCOW_TIMEZONE),
            )

            self.assertEqual(sent_count, 2)
            self.assertEqual(
                bot.messages,
                [
                    (
                        100,
                        "Наступил дедлайн по задаче:\n"
                        "02.06.2026\n#1 Оплатить интернет 18:30",
                    ),
                    (
                        200,
                        "Наступил дедлайн по задаче:\n"
                        "02.06.2026\n#1 Оплатить интернет 18:30",
                    ),
                ],
            )
            for reply_markup in bot.reply_markups:
                self.assertIsNotNone(reply_markup)
                keyboard = reply_markup.inline_keyboard
                self.assertEqual(len(keyboard), 2)
                self.assertEqual(keyboard[0][0].text, "Добавить")
                self.assertEqual(keyboard[0][0].callback_data, "todo:add")
                self.assertEqual(keyboard[0][1].text, "Списки")
                self.assertEqual(keyboard[0][1].callback_data, "todo:lists")
                self.assertEqual(keyboard[1][0].text, "Семья")
                self.assertEqual(keyboard[1][0].callback_data, "todo:family")
            with file_path.open("r", encoding="utf-8") as source:
                raw = json.load(source)
            self.assertEqual(raw[0]["deadline_notified_at"], "2026-06-02T18:30:00+03:00")
            self.assertIsNone(raw[1]["deadline_notified_at"])

    async def test_scheduler_sends_missed_morning_after_start(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "tasks.json"
            file_path.write_text(
                json.dumps(
                    [
                        {
                            "id": 1,
                            "chat_id": 100,
                            "text": "Купить молоко",
                            "deadline": "2026-06-02",
                            "created_at": "2026-06-01T09:00:00+00:00",
                        }
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            bot = FakeBot()
            storage = JsonTaskStorage(file_path=file_path)
            reminder_state = JsonReminderStateStorage(
                file_path=Path(temp_dir) / "reminder_state.json"
            )
            reminder_state.initialize()
            sleep_calls: list[float] = []
            now_values = iter(
                [
                    datetime(2026, 6, 2, 9, 5, tzinfo=MOSCOW_TIMEZONE),
                    datetime(2026, 6, 2, 9, 6, tzinfo=MOSCOW_TIMEZONE),
                ]
            )

            async def sleep(seconds: float) -> None:
                sleep_calls.append(seconds)
                if seconds == 0:
                    await asyncio.sleep(0)
                    return
                raise StopScheduler

            with patch("easy_task_manager.reminders.get_today_moscow", return_value=date(2026, 6, 2)):
                with self.assertRaises(StopScheduler):
                    await run_due_task_reminder_scheduler(
                        bot=bot,
                        storage=storage,
                        reminder_state=reminder_state,
                        sleep=sleep,
                        now_provider=lambda: next(now_values),
                    )

            self.assertEqual(sleep_calls[0], 0)
            self.assertEqual(
                bot.messages,
                [
                    (
                        100,
                        "Сегодня тебе надо сделать вот это:\n"
                        "02.06.2026\n#1 Купить молоко",
                    ),
                    (
                        200,
                        "Сегодня тебе надо сделать вот это:\n"
                        "02.06.2026\n#1 Купить молоко",
                    ),
                ],
            )
            self.assertTrue(
                reminder_state.is_daily_slot_processed(date(2026, 6, 2), "morning")
            )

    async def test_scheduler_sends_missed_evening_after_start(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "tasks.json"
            file_path.write_text(
                json.dumps(
                    [
                        {
                            "id": 1,
                            "chat_id": 100,
                            "text": "Вынести мусор",
                            "deadline": "2026-06-02",
                            "created_at": "2026-06-01T09:00:00+00:00",
                        }
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            bot = FakeBot()
            storage = JsonTaskStorage(file_path=file_path)
            reminder_state = JsonReminderStateStorage(
                file_path=Path(temp_dir) / "reminder_state.json"
            )
            reminder_state.initialize()
            sleep_calls: list[float] = []
            now_values = iter(
                [
                    datetime(2026, 6, 2, 18, 5, tzinfo=MOSCOW_TIMEZONE),
                    datetime(2026, 6, 2, 18, 6, tzinfo=MOSCOW_TIMEZONE),
                ]
            )

            async def sleep(seconds: float) -> None:
                sleep_calls.append(seconds)
                if seconds == 0:
                    await asyncio.sleep(0)
                    return
                raise StopScheduler

            with patch("easy_task_manager.reminders.get_today_moscow", return_value=date(2026, 6, 2)):
                with self.assertRaises(StopScheduler):
                    await run_due_task_reminder_scheduler(
                        bot=bot,
                        storage=storage,
                        reminder_state=reminder_state,
                        sleep=sleep,
                        now_provider=lambda: next(now_values),
                    )

            self.assertEqual(sleep_calls[0], 0)
            self.assertEqual(
                bot.messages,
                [
                    (
                        100,
                        "Тебе все ещё сегодня надо сделать это:\n"
                        "02.06.2026\n#1 Вынести мусор",
                    ),
                    (
                        200,
                        "Тебе все ещё сегодня надо сделать это:\n"
                        "02.06.2026\n#1 Вынести мусор",
                    ),
                ],
            )
            self.assertTrue(
                reminder_state.is_daily_slot_processed(date(2026, 6, 2), "morning")
            )
            self.assertTrue(
                reminder_state.is_daily_slot_processed(date(2026, 6, 2), "evening")
            )

    async def test_scheduler_does_not_duplicate_processed_morning_after_restart(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "tasks.json"
            file_path.write_text(
                json.dumps(
                    [
                        {
                            "id": 1,
                            "chat_id": 100,
                            "text": "Купить хлеб",
                            "deadline": "2026-06-02",
                            "created_at": "2026-06-01T09:00:00+00:00",
                        }
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            bot = FakeBot()
            storage = JsonTaskStorage(file_path=file_path)
            reminder_state = JsonReminderStateStorage(
                file_path=Path(temp_dir) / "reminder_state.json"
            )
            reminder_state.initialize()
            reminder_state.mark_daily_slot_processed(
                day=date(2026, 6, 2),
                slot_name="morning",
                processed_at=datetime(2026, 6, 2, 9, 5, tzinfo=MOSCOW_TIMEZONE),
            )

            async def sleep(seconds: float) -> None:
                raise StopScheduler

            with patch("easy_task_manager.reminders.get_today_moscow", return_value=date(2026, 6, 2)):
                with self.assertRaises(StopScheduler):
                    await run_due_task_reminder_scheduler(
                        bot=bot,
                        storage=storage,
                        reminder_state=reminder_state,
                        sleep=sleep,
                        now_provider=lambda: datetime(
                            2026,
                            6,
                            2,
                            9,
                            6,
                            tzinfo=MOSCOW_TIMEZONE,
                        ),
                    )

            self.assertEqual(bot.messages, [])

    async def test_scheduler_after_evening_sends_only_evening_when_both_slots_missed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "tasks.json"
            file_path.write_text(
                json.dumps(
                    [
                        {
                            "id": 1,
                            "chat_id": 100,
                            "text": "Позвонить врачу",
                            "deadline": "2026-06-02",
                            "created_at": "2026-06-01T09:00:00+00:00",
                        }
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            bot = FakeBot()
            storage = JsonTaskStorage(file_path=file_path)
            reminder_state = JsonReminderStateStorage(
                file_path=Path(temp_dir) / "reminder_state.json"
            )
            reminder_state.initialize()
            sleep_calls: list[float] = []
            now_values = iter(
                [
                    datetime(2026, 6, 2, 19, 0, tzinfo=MOSCOW_TIMEZONE),
                    datetime(2026, 6, 2, 19, 1, tzinfo=MOSCOW_TIMEZONE),
                ]
            )

            async def sleep(seconds: float) -> None:
                sleep_calls.append(seconds)
                if seconds == 0:
                    await asyncio.sleep(0)
                    return
                raise StopScheduler

            with patch("easy_task_manager.reminders.get_today_moscow", return_value=date(2026, 6, 2)):
                with self.assertRaises(StopScheduler):
                    await run_due_task_reminder_scheduler(
                        bot=bot,
                        storage=storage,
                        reminder_state=reminder_state,
                        sleep=sleep,
                        now_provider=lambda: next(now_values),
                    )

            self.assertEqual(sleep_calls[0], 0)
            self.assertEqual(len(bot.messages), 2)
            self.assertEqual(
                bot.messages[0][1],
                "Тебе все ещё сегодня надо сделать это:\n"
                "02.06.2026\n#1 Позвонить врачу",
            )
            self.assertEqual(bot.messages[1][1], bot.messages[0][1])
            self.assertTrue(
                reminder_state.is_daily_slot_processed(date(2026, 6, 2), "morning")
            )
            self.assertTrue(
                reminder_state.is_daily_slot_processed(date(2026, 6, 2), "evening")
            )

    async def test_scheduler_wakeup_reschedules_for_new_earlier_deadline(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "tasks.json"
            file_path.write_text("[]", encoding="utf-8")
            bot = FakeBot()
            storage = JsonTaskStorage(file_path=file_path)
            reminder_state = JsonReminderStateStorage(
                file_path=Path(temp_dir) / "reminder_state.json"
            )
            reminder_state.initialize()
            reminder_state.mark_daily_slot_processed(
                day=date(2026, 6, 2),
                slot_name="morning",
                processed_at=datetime(2026, 6, 2, 9, 0, tzinfo=MOSCOW_TIMEZONE),
            )
            wakeup_event = asyncio.Event()
            sleep_calls: list[float] = []
            now_values = iter(
                [
                    datetime(2026, 6, 2, 9, 1, tzinfo=MOSCOW_TIMEZONE),
                    datetime(2026, 6, 2, 13, 15, tzinfo=MOSCOW_TIMEZONE),
                    datetime(2026, 6, 2, 13, 16, tzinfo=MOSCOW_TIMEZONE),
                ]
            )

            async def sleep(seconds: float) -> None:
                sleep_calls.append(seconds)
                if len(sleep_calls) == 1:
                    file_path.write_text(
                        json.dumps(
                            [
                                {
                                    "id": 1,
                                    "chat_id": 100,
                                    "text": "Срочная задача",
                                    "deadline": "2026-06-02",
                                    "deadline_time": "13:15",
                                    "deadline_notified_at": None,
                                    "created_at": "2026-06-01T09:00:00+00:00",
                                }
                            ],
                            ensure_ascii=False,
                        ),
                        encoding="utf-8",
                    )
                    wakeup_event.set()
                    await asyncio.sleep(0)
                    return
                if seconds == 0:
                    await asyncio.sleep(0)
                    return
                raise StopScheduler

            with self.assertRaises(StopScheduler):
                await run_due_task_reminder_scheduler(
                    bot=bot,
                    storage=storage,
                    reminder_state=reminder_state,
                    sleep=sleep,
                    now_provider=lambda: next(now_values),
                    wakeup_event=wakeup_event,
                )

            self.assertGreater(sleep_calls[0], 0)
            self.assertEqual(sleep_calls[1], 0)
            self.assertEqual(
                bot.messages,
                [
                    (
                        100,
                        "Наступил дедлайн по задаче:\n"
                        "02.06.2026\n#1 Срочная задача 13:15",
                    ),
                    (
                        200,
                        "Наступил дедлайн по задаче:\n"
                        "02.06.2026\n#1 Срочная задача 13:15",
                    ),
                ],
            )


class ReminderScheduleTests(unittest.TestCase):
    def test_get_next_reminder_run_before_morning(self) -> None:
        planned_at, slot = _get_next_reminder_run(
            datetime(2026, 6, 2, 8, 30, tzinfo=MOSCOW_TIMEZONE)
        )

        self.assertEqual(slot.name, "morning")
        self.assertEqual(planned_at, datetime(2026, 6, 2, 9, 0, tzinfo=MOSCOW_TIMEZONE))

    def test_get_next_reminder_run_between_slots(self) -> None:
        planned_at, slot = _get_next_reminder_run(
            datetime(2026, 6, 2, 9, 1, tzinfo=MOSCOW_TIMEZONE)
        )

        self.assertEqual(slot.name, "evening")
        self.assertEqual(planned_at, datetime(2026, 6, 2, 18, 0, tzinfo=MOSCOW_TIMEZONE))

    def test_get_next_reminder_run_after_evening(self) -> None:
        planned_at, slot = _get_next_reminder_run(
            datetime(2026, 6, 2, 18, 1, tzinfo=MOSCOW_TIMEZONE)
        )

        self.assertEqual(slot.name, "morning")
        self.assertEqual(planned_at, datetime(2026, 6, 3, 9, 0, tzinfo=MOSCOW_TIMEZONE))

    def test_get_next_scheduler_run_prefers_nearest_exact_deadline(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "tasks.json"
            file_path.write_text(
                json.dumps(
                    [
                        {
                            "id": 1,
                            "chat_id": 100,
                            "text": "В середине дня",
                            "deadline": "2026-06-02",
                            "deadline_time": "13:15",
                            "deadline_notified_at": None,
                            "created_at": "2026-06-01T09:00:00+00:00",
                        }
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            storage = JsonTaskStorage(file_path=file_path)

            planned_at, slot = _get_next_scheduler_run(
                now=datetime(2026, 6, 2, 9, 1, tzinfo=MOSCOW_TIMEZONE),
                storage=storage,
            )

            self.assertIsNone(slot)
            self.assertEqual(planned_at, datetime(2026, 6, 2, 13, 15, tzinfo=MOSCOW_TIMEZONE))


if __name__ == "__main__":
    unittest.main()
