import unittest
from datetime import date

from easy_task_manager.recurrence import (
    RECURRENCE_DAILY,
    RECURRENCE_MONTHLY,
    RECURRENCE_WEEKLY,
    calculate_next_deadline,
)


class RecurrenceTests(unittest.TestCase):
    def test_calculate_next_daily_deadline(self) -> None:
        self.assertEqual(
            calculate_next_deadline(
                deadline=date(2026, 6, 10),
                recurrence=RECURRENCE_DAILY,
                today=date(2026, 6, 10),
            ),
            date(2026, 6, 11),
        )

    def test_calculate_next_weekly_deadline_skips_overdue_dates(self) -> None:
        self.assertEqual(
            calculate_next_deadline(
                deadline=date(2026, 6, 1),
                recurrence=RECURRENCE_WEEKLY,
                today=date(2026, 6, 20),
            ),
            date(2026, 6, 22),
        )

    def test_calculate_next_monthly_deadline_keeps_anchor_day(self) -> None:
        self.assertEqual(
            calculate_next_deadline(
                deadline=date(2026, 1, 31),
                recurrence=RECURRENCE_MONTHLY,
                today=date(2026, 1, 31),
                anchor_day=31,
            ),
            date(2026, 2, 28),
        )
        self.assertEqual(
            calculate_next_deadline(
                deadline=date(2026, 2, 28),
                recurrence=RECURRENCE_MONTHLY,
                today=date(2026, 2, 28),
                anchor_day=31,
            ),
            date(2026, 3, 31),
        )


if __name__ == "__main__":
    unittest.main()
