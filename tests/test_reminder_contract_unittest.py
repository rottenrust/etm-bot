import unittest
from datetime import date, datetime, time, timezone

from easy_task_manager.reminder_contract import (
    build_exact_deadline_reminder_text,
    build_evening_reminder_text,
    build_morning_reminder_text,
)
from easy_task_manager.task_storage import Task


class ReminderContractTests(unittest.TestCase):
    def test_build_morning_reminder_text(self) -> None:
        task = Task(
            id=1,
            chat_id=100,
            text="Купить молоко",
            deadline=date(2026, 6, 2),
            deadline_time=time(18, 30),
            created_at=datetime.now(timezone.utc),
        )

        self.assertEqual(
            build_morning_reminder_text([task]),
            "Сегодня тебе надо сделать вот это:\n"
            "02.06.2026\n#1 Купить молоко 18:30",
        )

    def test_build_evening_reminder_text(self) -> None:
        task = Task(
            id=2,
            chat_id=100,
            text="Оплатить интернет",
            deadline=date(2026, 6, 1),
            created_at=datetime.now(timezone.utc),
        )

        self.assertEqual(
            build_evening_reminder_text([task]),
            "Тебе все ещё сегодня надо сделать это:\n"
            "01.06.2026\n#2 Оплатить интернет",
        )

    def test_build_reminder_text_returns_empty_text_without_tasks(self) -> None:
        self.assertEqual(build_morning_reminder_text([]), "")
        self.assertEqual(build_evening_reminder_text([]), "")

    def test_build_exact_deadline_reminder_text(self) -> None:
        task = Task(
            id=3,
            chat_id=100,
            text="Оплатить интернет",
            deadline=date(2026, 6, 2),
            deadline_time=time(18, 30),
            created_at=datetime.now(timezone.utc),
        )

        self.assertEqual(
            build_exact_deadline_reminder_text([task]),
            "Наступил дедлайн по задаче:\n"
            "02.06.2026\n#3 Оплатить интернет 18:30",
        )


if __name__ == "__main__":
    unittest.main()
