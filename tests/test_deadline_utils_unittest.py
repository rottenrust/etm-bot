import unittest
from datetime import date, datetime, time

from easy_task_manager.deadline_utils import (
    format_deadline_for_user,
    is_past_deadline,
    is_past_deadline_time,
    parse_custom_deadline,
    parse_deadline_time,
)


class DeadlineUtilsTests(unittest.TestCase):
    def test_parse_custom_deadline_valid(self) -> None:
        parsed = parse_custom_deadline("01.06.2026")
        self.assertEqual(parsed, date(2026, 6, 1))

    def test_parse_custom_deadline_invalid(self) -> None:
        with self.assertRaises(ValueError):
            parse_custom_deadline("31.02.2026")

    def test_parse_deadline_time_valid(self) -> None:
        parsed = parse_deadline_time("18:30")
        self.assertEqual(parsed, time(18, 30))

    def test_parse_deadline_time_invalid(self) -> None:
        with self.assertRaises(ValueError):
            parse_deadline_time("8:30")

    def test_is_past_deadline(self) -> None:
        self.assertTrue(is_past_deadline(date(2026, 5, 31), today=date(2026, 6, 1)))
        self.assertFalse(is_past_deadline(date(2026, 6, 1), today=date(2026, 6, 1)))

    def test_is_past_deadline_time(self) -> None:
        now = datetime(2026, 6, 1, 18, 0)
        self.assertTrue(is_past_deadline_time(date(2026, 6, 1), time(17, 59), now=now))
        self.assertFalse(is_past_deadline_time(date(2026, 6, 1), time(18, 1), now=now))

    def test_format_deadline_for_user(self) -> None:
        self.assertEqual(format_deadline_for_user(date(2026, 6, 1)), "01.06.2026")
        self.assertEqual(
            format_deadline_for_user(date(2026, 6, 1), time(18, 30)),
            "01.06.2026 18:30",
        )


if __name__ == "__main__":
    unittest.main()
