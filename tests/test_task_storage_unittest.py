import json
import tempfile
import unittest
from datetime import date, datetime, time, timezone
from pathlib import Path

from easy_task_manager.task_storage import JsonTaskStorage


class JsonTaskStorageTests(unittest.TestCase):
    def test_initialize_creates_empty_tasks_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "data" / "tasks.json"
            storage = JsonTaskStorage(file_path=file_path)

            storage.initialize()

            self.assertTrue(file_path.exists())
            with file_path.open("r", encoding="utf-8") as source:
                raw = json.load(source)
            self.assertEqual(raw, [])

    def test_initialize_keeps_existing_tasks_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "tasks.json"
            existing_tasks = [
                {
                    "id": 1,
                    "chat_id": 100,
                    "text": "Купить молоко",
                    "deadline": None,
                    "created_at": "2026-06-01T09:00:00+00:00",
                }
            ]
            file_path.write_text(
                json.dumps(existing_tasks, ensure_ascii=False),
                encoding="utf-8",
            )
            storage = JsonTaskStorage(file_path=file_path)

            storage.initialize()

            with file_path.open("r", encoding="utf-8") as source:
                raw = json.load(source)
            self.assertEqual(raw, existing_tasks)

    def test_add_task_persists_to_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "tasks.json"
            storage = JsonTaskStorage(file_path=file_path)

            created = storage.add_task(
                chat_id=1001,
                text="Купить молоко",
                deadline=date(2026, 6, 2),
                deadline_time=time(18, 30),
            )

            self.assertEqual(created.id, 1)
            self.assertEqual(created.chat_id, 1001)
            self.assertEqual(created.text, "Купить молоко")
            self.assertEqual(created.deadline, date(2026, 6, 2))
            self.assertEqual(created.deadline_time, time(18, 30))
            self.assertEqual(created.list_id, "general")

            with file_path.open("r", encoding="utf-8") as source:
                raw = json.load(source)
            self.assertEqual(len(raw), 1)
            self.assertEqual(raw[0]["id"], 1)
            self.assertEqual(raw[0]["chat_id"], 1001)
            self.assertEqual(raw[0]["text"], "Купить молоко")
            self.assertEqual(raw[0]["list_id"], "general")
            self.assertEqual(raw[0]["deadline"], "2026-06-02")
            self.assertEqual(raw[0]["deadline_time"], "18:30")
            self.assertIsNone(raw[0]["deadline_notified_at"])
            self.assertIsNone(raw[0]["recurrence"])

    def test_add_task_persists_recurrence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "tasks.json"
            storage = JsonTaskStorage(file_path=file_path)

            created = storage.add_task(
                chat_id=1001,
                text="Оплатить интернет",
                deadline=date(2026, 6, 25),
                recurrence="monthly",
            )

            self.assertEqual(created.recurrence, "monthly")
            self.assertEqual(created.recurrence_anchor_day, 25)
            with file_path.open("r", encoding="utf-8") as source:
                raw = json.load(source)
            self.assertEqual(raw[0]["recurrence"], "monthly")
            self.assertEqual(raw[0]["recurrence_anchor_day"], 25)

    def test_add_task_increments_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "tasks.json"
            storage = JsonTaskStorage(file_path=file_path)
            storage.add_task(chat_id=1, text="Первая", deadline=None)
            second = storage.add_task(chat_id=1, text="Вторая", deadline=None)
            self.assertEqual(second.id, 2)

    def test_list_tasks_by_family_includes_tasks_from_different_chats(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "tasks.json"
            storage = JsonTaskStorage(file_path=file_path)
            storage.add_task(chat_id=100, text="Купить молоко", deadline=None)
            storage.add_task(chat_id=200, text="Оплатить интернет", deadline=None)

            tasks = storage.list_tasks_by_family(family_id="default")

            self.assertEqual([task.text for task in tasks], ["Купить молоко", "Оплатить интернет"])
            self.assertEqual([task.chat_id for task in tasks], [100, 200])

    def test_list_tasks_by_family_reads_legacy_tasks_without_family_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "tasks.json"
            file_path.write_text(
                json.dumps(
                    [
                        {
                            "id": 1,
                            "chat_id": 100,
                            "text": "Старая задача",
                            "deadline": None,
                            "created_at": "2026-06-01T09:00:00+00:00",
                        }
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            storage = JsonTaskStorage(file_path=file_path)
            tasks = storage.list_tasks_by_family(family_id="default")

            self.assertEqual(len(tasks), 1)
            self.assertEqual(tasks[0].text, "Старая задача")
            self.assertEqual(tasks[0].list_id, "general")
            self.assertIsNone(tasks[0].recurrence)
            self.assertIsNone(tasks[0].snoozed_until)
            self.assertIsNone(tasks[0].note)
            self.assertTrue(tasks[0].reminder_enabled)
            self.assertIsNone(tasks[0].completed_at)

    def test_completed_task_is_hidden_from_active_family_lists(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "tasks.json"
            storage = JsonTaskStorage(file_path=file_path)
            task = storage.add_task(
                chat_id=100,
                text="Купить молоко",
                deadline=None,
                family_id="family-1",
                list_id="shopping",
            )

            completed = storage.complete_task_by_family(
                family_id="family-1",
                task_id=task.id,
                completed_at=datetime(2026, 6, 20, 9, 0, tzinfo=timezone.utc),
            )

            self.assertIsNotNone(completed)
            self.assertEqual(storage.list_tasks_by_family(family_id="family-1"), [])
            self.assertEqual(
                storage.count_tasks_by_family_lists(family_id="family-1"),
                {},
            )

    def test_add_task_persists_note_and_disabled_reminder(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "tasks.json"
            storage = JsonTaskStorage(file_path=file_path)

            created = storage.add_task(
                chat_id=100,
                text="Тренировка",
                deadline=date(2026, 6, 20),
                deadline_time=time(16, 0),
                note="Бедра и ягодицы",
                reminder_enabled=False,
            )

            self.assertEqual(created.note, "Бедра и ягодицы")
            self.assertFalse(created.reminder_enabled)
            due = storage.list_timed_due_tasks_by_family(
                now=datetime(2026, 6, 20, 16, 1, tzinfo=timezone.utc),
            )
            self.assertEqual(due, {})

    def test_list_tasks_by_family_and_list_hides_future_snoozed_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "tasks.json"
            storage = JsonTaskStorage(file_path=file_path)
            active = storage.add_task(
                chat_id=100,
                text="Купить молоко",
                deadline=None,
                family_id="family-1",
                list_id="shopping",
            )
            snoozed = storage.add_task(
                chat_id=100,
                text="Купить фильтр",
                deadline=date(2026, 6, 25),
                family_id="family-1",
                list_id="shopping",
            )

            updated = storage.update_task_snooze_by_family(
                family_id="family-1",
                task_id=snoozed.id,
                snoozed_until=datetime(2026, 6, 20, 9, 0, tzinfo=timezone.utc),
            )

            tasks = storage.list_tasks_by_family_and_list(
                family_id="family-1",
                list_id="shopping",
                now=datetime(2026, 6, 19, 12, 0, tzinfo=timezone.utc),
            )
            snoozed_tasks = storage.list_snoozed_tasks_by_family_and_list(
                family_id="family-1",
                list_id="shopping",
                now=datetime(2026, 6, 19, 12, 0, tzinfo=timezone.utc),
            )

            self.assertIsNotNone(updated)
            self.assertEqual([task.id for task in tasks], [active.id])
            self.assertEqual([task.id for task in snoozed_tasks], [snoozed.id])
            self.assertEqual(updated.deadline, date(2026, 6, 25))

    def test_snoozed_task_returns_to_active_list_after_snooze_date(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "tasks.json"
            storage = JsonTaskStorage(file_path=file_path)
            task = storage.add_task(
                chat_id=100,
                text="Купить фильтр",
                deadline=None,
                family_id="family-1",
                list_id="shopping",
            )
            storage.update_task_snooze_by_family(
                family_id="family-1",
                task_id=task.id,
                snoozed_until=datetime(2026, 6, 20, 9, 0, tzinfo=timezone.utc),
            )

            active_tasks = storage.list_tasks_by_family_and_list(
                family_id="family-1",
                list_id="shopping",
                now=datetime(2026, 6, 20, 9, 0, tzinfo=timezone.utc),
            )
            snoozed_tasks = storage.list_snoozed_tasks_by_family_and_list(
                family_id="family-1",
                list_id="shopping",
                now=datetime(2026, 6, 20, 9, 0, tzinfo=timezone.utc),
            )

            self.assertEqual([item.id for item in active_tasks], [task.id])
            self.assertEqual(snoozed_tasks, [])

    def test_list_tasks_ignores_invalid_recurrence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "tasks.json"
            file_path.write_text(
                json.dumps(
                    [
                        {
                            "id": 1,
                            "chat_id": 100,
                            "text": "Старая задача",
                            "deadline": "2026-06-02",
                            "recurrence": "yearly",
                            "created_at": "2026-06-01T09:00:00+00:00",
                        }
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            storage = JsonTaskStorage(file_path=file_path)
            tasks = storage.list_tasks_by_family(family_id="default")

            self.assertEqual(len(tasks), 1)
            self.assertIsNone(tasks[0].recurrence)

    def test_add_task_can_persist_specific_task_list(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "tasks.json"
            storage = JsonTaskStorage(file_path=file_path)

            created = storage.add_task(
                chat_id=100,
                text="Купить краску",
                deadline=None,
                family_id="family-1",
                list_id="dacha",
            )

            self.assertEqual(created.list_id, "dacha")
            with file_path.open("r", encoding="utf-8") as source:
                raw = json.load(source)
            self.assertEqual(raw[0]["list_id"], "dacha")

    def test_list_tasks_by_family_and_list_filters_topics(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "tasks.json"
            storage = JsonTaskStorage(file_path=file_path)
            storage.add_task(
                chat_id=100,
                text="Купить молоко",
                deadline=None,
                family_id="family-1",
                list_id="shopping",
            )
            storage.add_task(
                chat_id=100,
                text="Починить розетку",
                deadline=None,
                family_id="family-1",
                list_id="home",
            )
            storage.add_task(
                chat_id=200,
                text="Чужая покупка",
                deadline=None,
                family_id="family-2",
                list_id="shopping",
            )

            tasks = storage.list_tasks_by_family_and_list(
                family_id="family-1",
                list_id="shopping",
            )

            self.assertEqual([task.text for task in tasks], ["Купить молоко"])

    def test_update_task_list_by_family_moves_only_family_task(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "tasks.json"
            storage = JsonTaskStorage(file_path=file_path)
            task = storage.add_task(
                chat_id=100,
                text="Подготовить отчет",
                deadline=None,
                family_id="family-1",
                list_id="general",
            )
            storage.add_task(
                chat_id=200,
                text="Чужая задача",
                deadline=None,
                family_id="family-2",
                list_id="general",
            )

            updated = storage.update_task_list_by_family(
                family_id="family-1",
                task_id=task.id,
                list_id="work",
            )
            missing = storage.update_task_list_by_family(
                family_id="family-2",
                task_id=task.id,
                list_id="shopping",
            )

            self.assertIsNotNone(updated)
            self.assertEqual(updated.list_id, "work")
            self.assertIsNone(missing)
            self.assertEqual(
                storage.get_task_by_family("family-1", task.id).list_id,
                "work",
            )

    def test_update_task_recurrence_by_family_can_set_and_remove(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "tasks.json"
            storage = JsonTaskStorage(file_path=file_path)
            task = storage.add_task(
                chat_id=100,
                text="Оплатить интернет",
                deadline=date(2026, 6, 25),
                family_id="family-1",
            )

            updated = storage.update_task_recurrence_by_family(
                family_id="family-1",
                task_id=task.id,
                recurrence="monthly",
            )
            removed = storage.update_task_recurrence_by_family(
                family_id="family-1",
                task_id=task.id,
                recurrence=None,
            )

            self.assertIsNotNone(updated)
            self.assertEqual(updated.recurrence, "monthly")
            self.assertEqual(updated.recurrence_anchor_day, 25)
            self.assertIsNotNone(removed)
            self.assertIsNone(removed.recurrence)
            self.assertIsNone(removed.recurrence_anchor_day)

    def test_update_deadline_removes_recurrence_when_deadline_removed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "tasks.json"
            storage = JsonTaskStorage(file_path=file_path)
            task = storage.add_task(
                chat_id=100,
                text="Оплатить интернет",
                deadline=date(2026, 6, 25),
                family_id="family-1",
                recurrence="monthly",
            )

            updated = storage.update_task_deadline_by_family(
                family_id="family-1",
                task_id=task.id,
                deadline=None,
            )

            self.assertIsNotNone(updated)
            self.assertIsNone(updated.deadline)
            self.assertIsNone(updated.recurrence)

    def test_list_tasks_by_chat_filters_and_sorts_by_deadline_then_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "tasks.json"
            file_path.write_text(
                json.dumps(
                    [
                        {
                            "id": 4,
                            "chat_id": 100,
                            "text": "Без дедлайна",
                            "deadline": None,
                            "created_at": "2026-06-01T10:00:00+00:00",
                        },
                        {
                            "id": 1,
                            "chat_id": 200,
                            "text": "Чужая",
                            "deadline": None,
                            "created_at": "2026-06-01T09:00:00+00:00",
                        },
                        {
                            "id": 2,
                            "chat_id": 100,
                            "text": "Позже",
                            "deadline": "2026-06-10",
                            "created_at": "2026-06-01T09:30:00+00:00",
                        },
                        {
                            "id": 3,
                            "chat_id": 100,
                            "text": "Раньше",
                            "deadline": "2026-06-02",
                            "created_at": "2026-06-01T09:45:00+00:00",
                        },
                        {
                            "id": 5,
                            "chat_id": 100,
                            "text": "Та же дата позже по id",
                            "deadline": "2026-06-02",
                            "deadline_time": "18:30",
                            "created_at": "2026-06-01T10:30:00+00:00",
                        },
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            storage = JsonTaskStorage(file_path=file_path)
            tasks = storage.list_tasks_by_chat(chat_id=100)

            self.assertEqual([task.id for task in tasks], [5, 3, 2, 4])
            self.assertEqual(
                [task.text for task in tasks],
                ["Та же дата позже по id", "Раньше", "Позже", "Без дедлайна"],
            )

    def test_list_due_tasks_by_chat_includes_today_and_overdue_tasks(self) -> None:
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
                            "created_at": "2026-06-01T09:30:00+00:00",
                        },
                        {
                            "id": 3,
                            "chat_id": 100,
                            "text": "Будущая",
                            "deadline": "2026-06-03",
                            "created_at": "2026-06-01T10:00:00+00:00",
                        },
                        {
                            "id": 4,
                            "chat_id": 100,
                            "text": "Без дедлайна",
                            "deadline": None,
                            "created_at": "2026-06-01T10:30:00+00:00",
                        },
                        {
                            "id": 5,
                            "chat_id": 200,
                            "text": "В другом чате",
                            "deadline": "2026-06-02",
                            "created_at": "2026-06-01T11:00:00+00:00",
                        },
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            storage = JsonTaskStorage(file_path=file_path)
            due_tasks = storage.list_due_tasks_by_chat(today=date(2026, 6, 2))

            self.assertEqual(sorted(due_tasks.keys()), [100, 200])
            self.assertEqual([task.id for task in due_tasks[100]], [1, 2])
            self.assertEqual([task.id for task in due_tasks[200]], [5])

    def test_list_tasks_reads_legacy_tasks_without_deadline_time(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "tasks.json"
            file_path.write_text(
                json.dumps(
                    [
                        {
                            "id": 1,
                            "chat_id": 100,
                            "text": "Старая задача",
                            "deadline": "2026-06-02",
                            "created_at": "2026-06-01T09:00:00+00:00",
                        }
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            storage = JsonTaskStorage(file_path=file_path)
            tasks = storage.list_tasks_by_chat(chat_id=100)

            self.assertEqual(len(tasks), 1)
            self.assertEqual(tasks[0].deadline, date(2026, 6, 2))
            self.assertIsNone(tasks[0].deadline_time)

    def test_list_timed_due_tasks_by_chat_returns_reached_unnotified_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "tasks.json"
            file_path.write_text(
                json.dumps(
                    [
                        {
                            "id": 1,
                            "chat_id": 100,
                            "text": "Уже пора",
                            "deadline": "2026-06-02",
                            "deadline_time": "18:00",
                            "deadline_notified_at": None,
                            "created_at": "2026-06-01T09:00:00+00:00",
                        },
                        {
                            "id": 2,
                            "chat_id": 100,
                            "text": "Ещё рано",
                            "deadline": "2026-06-02",
                            "deadline_time": "18:31",
                            "deadline_notified_at": None,
                            "created_at": "2026-06-01T09:00:00+00:00",
                        },
                        {
                            "id": 3,
                            "chat_id": 100,
                            "text": "Уже отправляли",
                            "deadline": "2026-06-02",
                            "deadline_time": "17:00",
                            "deadline_notified_at": "2026-06-02T17:00:00+03:00",
                            "created_at": "2026-06-01T09:00:00+00:00",
                        },
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            storage = JsonTaskStorage(file_path=file_path)
            due_tasks = storage.list_timed_due_tasks_by_chat(
                now=datetime(2026, 6, 2, 18, 30),
            )

            self.assertEqual([task.id for task in due_tasks[100]], [1])

    def test_mark_deadline_notifications_sent_updates_matching_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "tasks.json"
            file_path.write_text(
                json.dumps(
                    [
                        {
                            "id": 1,
                            "chat_id": 100,
                            "text": "Пора",
                            "deadline": "2026-06-02",
                            "deadline_time": "18:00",
                            "deadline_notified_at": None,
                            "created_at": "2026-06-01T09:00:00+00:00",
                        },
                        {
                            "id": 1,
                            "chat_id": 200,
                            "text": "Чужая",
                            "deadline": "2026-06-02",
                            "deadline_time": "18:00",
                            "deadline_notified_at": None,
                            "created_at": "2026-06-01T09:00:00+00:00",
                        },
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            storage = JsonTaskStorage(file_path=file_path)
            updated = storage.mark_deadline_notifications_sent(
                chat_id=100,
                task_ids=[1],
                notified_at=datetime(2026, 6, 2, 18, 0),
            )

            self.assertEqual(updated, 1)
            with file_path.open("r", encoding="utf-8") as source:
                raw = json.load(source)
            self.assertEqual(raw[0]["deadline_notified_at"], "2026-06-02T18:00:00")
            self.assertIsNone(raw[1]["deadline_notified_at"])

    def test_get_next_timed_deadline_at_returns_nearest_pending_time(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "tasks.json"
            file_path.write_text(
                json.dumps(
                    [
                        {
                            "id": 1,
                            "chat_id": 100,
                            "text": "Позже",
                            "deadline": "2026-06-02",
                            "deadline_time": "19:00",
                            "deadline_notified_at": None,
                            "created_at": "2026-06-01T09:00:00+00:00",
                        },
                        {
                            "id": 2,
                            "chat_id": 100,
                            "text": "Ближе",
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

            storage = JsonTaskStorage(file_path=file_path)

            self.assertEqual(
                storage.get_next_timed_deadline_at(now=datetime(2026, 6, 2, 18, 30)),
                datetime(2026, 6, 2, 18, 45),
            )

    def test_update_task_deadline_by_chat_updates_matching_task(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "tasks.json"
            file_path.write_text(
                json.dumps(
                    [
                        {
                            "id": 1,
                            "chat_id": 100,
                            "text": "Оплатить интернет",
                            "deadline": None,
                            "deadline_time": None,
                            "deadline_notified_at": "2026-06-02T18:00:00+03:00",
                            "created_at": "2026-06-01T09:00:00+00:00",
                        },
                        {
                            "id": 1,
                            "chat_id": 200,
                            "text": "Чужая задача",
                            "deadline": None,
                            "created_at": "2026-06-01T09:30:00+00:00",
                        },
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            storage = JsonTaskStorage(file_path=file_path)
            updated = storage.update_task_deadline_by_chat(
                chat_id=100,
                task_id=1,
                deadline=date(2026, 6, 3),
                deadline_time=time(18, 30),
            )

            self.assertTrue(updated)
            with file_path.open("r", encoding="utf-8") as source:
                raw = json.load(source)
            self.assertEqual(raw[0]["deadline"], "2026-06-03")
            self.assertEqual(raw[0]["deadline_time"], "18:30")
            self.assertIsNone(raw[0]["deadline_notified_at"])
            self.assertIsNone(raw[1]["deadline"])

    def test_update_task_deadline_by_chat_removes_deadline(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "tasks.json"
            file_path.write_text(
                json.dumps(
                    [
                        {
                            "id": 1,
                            "chat_id": 100,
                            "text": "Оплатить интернет",
                            "deadline": "2026-06-03",
                            "deadline_time": "18:30",
                            "deadline_notified_at": "2026-06-03T18:30:00+03:00",
                            "created_at": "2026-06-01T09:00:00+00:00",
                        }
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            storage = JsonTaskStorage(file_path=file_path)
            updated = storage.update_task_deadline_by_chat(
                chat_id=100,
                task_id=1,
                deadline=None,
            )

            self.assertTrue(updated)
            with file_path.open("r", encoding="utf-8") as source:
                raw = json.load(source)
            self.assertIsNone(raw[0]["deadline"])
            self.assertIsNone(raw[0]["deadline_time"])
            self.assertIsNone(raw[0]["deadline_notified_at"])

    def test_update_task_deadline_by_chat_returns_false_when_not_found(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "tasks.json"
            storage = JsonTaskStorage(file_path=file_path)

            self.assertFalse(
                storage.update_task_deadline_by_chat(
                    chat_id=100,
                    task_id=1,
                    deadline=date(2026, 6, 3),
                )
            )

    def test_delete_task_by_chat_removes_only_matching_task(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "tasks.json"
            file_path.write_text(
                json.dumps(
                    [
                        {
                            "id": 1,
                            "chat_id": 100,
                            "text": "Купить молоко",
                            "deadline": None,
                            "created_at": "2026-06-01T09:00:00+00:00",
                        },
                        {
                            "id": 1,
                            "chat_id": 200,
                            "text": "Чужая задача с тем же номером",
                            "deadline": None,
                            "created_at": "2026-06-01T09:30:00+00:00",
                        },
                        {
                            "id": 2,
                            "chat_id": 100,
                            "text": "Оплатить интернет",
                            "deadline": "2026-06-02",
                            "created_at": "2026-06-01T10:00:00+00:00",
                        },
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            storage = JsonTaskStorage(file_path=file_path)
            deleted = storage.delete_task_by_chat(chat_id=100, task_id=1)

            self.assertTrue(deleted)
            remaining_for_chat_100 = storage.list_tasks_by_chat(chat_id=100)
            remaining_for_chat_200 = storage.list_tasks_by_chat(chat_id=200)
            self.assertEqual([task.id for task in remaining_for_chat_100], [2])
            self.assertEqual([task.id for task in remaining_for_chat_200], [1])

    def test_delete_task_by_chat_returns_false_when_not_found(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "tasks.json"
            storage = JsonTaskStorage(file_path=file_path)

            self.assertFalse(storage.delete_task_by_chat(chat_id=100, task_id=1))

    def test_delete_tasks_by_family_removes_only_matching_family(self) -> None:
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
                            "deadline": None,
                            "created_at": "2026-06-01T09:00:00+00:00",
                        },
                        {
                            "id": 2,
                            "family_id": "family_b",
                            "chat_id": 200,
                            "text": "Оплатить интернет",
                            "deadline": None,
                            "created_at": "2026-06-01T10:00:00+00:00",
                        },
                        {
                            "id": 3,
                            "family_id": "family_a",
                            "chat_id": 101,
                            "text": "Забрать заказ",
                            "deadline": "2026-06-02",
                            "created_at": "2026-06-01T11:00:00+00:00",
                        },
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            storage = JsonTaskStorage(file_path=file_path)

            deleted_count = storage.delete_tasks_by_family("family_a")

            self.assertEqual(deleted_count, 2)
            self.assertEqual([task.text for task in storage.list_tasks_by_family("family_a")], [])
            self.assertEqual(
                [task.text for task in storage.list_tasks_by_family("family_b")],
                ["Оплатить интернет"],
            )


if __name__ == "__main__":
    unittest.main()
