import unittest
from datetime import date, datetime, time, timezone

from easy_task_manager.list_tasks_contract import (
    LIST_EMPTY_TEXT,
    SNOOZED_LIST_EMPTY_TEXT,
    build_snoozed_task_list_text,
    build_task_done_callback,
    build_task_page,
    build_task_page_callback,
    build_task_page_hint_text,
    build_task_hint_callback,
    build_task_list_text,
    build_task_back_callback,
    build_task_snooze_menu_callback,
    build_task_snoozed_back_callback,
    build_task_snoozed_hint_callback,
    build_task_snoozed_page_callback,
    format_task_line,
    parse_task_back_context,
    parse_task_hint_context,
    parse_task_page_callback,
    parse_task_snoozed_back_context,
    parse_task_snoozed_hint_context,
    parse_task_snoozed_page_callback,
)
from easy_task_manager.task_storage import Task


class ListTasksContractTests(unittest.TestCase):
    def test_format_task_line_with_deadline(self) -> None:
        task = Task(
            id=1,
            chat_id=100,
            text="Купить молоко",
            deadline=date(2026, 6, 2),
            deadline_time=time(18, 30),
            created_at=datetime.now(timezone.utc),
        )
        self.assertEqual(
            format_task_line(task),
            "#1 Купить молоко 18:30",
        )

    def test_format_task_line_without_deadline(self) -> None:
        task = Task(
            id=2,
            chat_id=100,
            text="Постирать",
            deadline=None,
            created_at=datetime.now(timezone.utc),
        )
        self.assertEqual(format_task_line(task), "#2 Постирать")

    def test_format_task_line_with_recurrence(self) -> None:
        task = Task(
            id=3,
            chat_id=100,
            text="Оплатить интернет",
            deadline=date(2026, 6, 25),
            created_at=datetime.now(timezone.utc),
            recurrence="monthly",
        )
        self.assertEqual(
            format_task_line(task),
            "#3 Оплатить интернет (каждый месяц)",
        )

    def test_build_task_list_text_empty(self) -> None:
        self.assertEqual(build_task_list_text([]), LIST_EMPTY_TEXT)

    def test_build_snoozed_task_list_text_shows_snooze_date(self) -> None:
        task = Task(
            id=7,
            chat_id=100,
            text="Купить фильтр",
            deadline=date(2026, 6, 25),
            created_at=datetime.now(timezone.utc),
            snoozed_until=datetime(2026, 6, 20, 9, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(
            build_snoozed_task_list_text([task]),
            "Отложено до 20.06.2026 12:00\n#7 Купить фильтр",
        )
        self.assertEqual(build_snoozed_task_list_text([]), SNOOZED_LIST_EMPTY_TEXT)

    def test_build_task_list_text_multiple_rows(self) -> None:
        tasks = [
            Task(
                id=1,
                chat_id=100,
                text="Купить молоко",
                deadline=date(2026, 6, 2),
                created_at=datetime.now(timezone.utc),
            ),
            Task(
                id=2,
                chat_id=100,
                text="Постирать",
                deadline=None,
                created_at=datetime.now(timezone.utc),
            ),
        ]

        self.assertEqual(
            build_task_list_text(tasks),
            "02.06.2026\n#1 Купить молоко\n\nБез дедлайна\n#2 Постирать",
        )

    def test_build_task_list_text_groups_and_sorts_by_deadline(self) -> None:
        tasks = [
            Task(
                id=5,
                chat_id=100,
                text="Без дедлайна позже",
                deadline=None,
                created_at=datetime.now(timezone.utc),
            ),
            Task(
                id=3,
                chat_id=100,
                text="Сегодня без времени",
                deadline=date(2026, 6, 2),
                created_at=datetime.now(timezone.utc),
            ),
            Task(
                id=2,
                chat_id=100,
                text="Сегодня утром",
                deadline=date(2026, 6, 2),
                deadline_time=time(9, 0),
                created_at=datetime.now(timezone.utc),
            ),
            Task(
                id=4,
                chat_id=100,
                text="Без дедлайна раньше",
                deadline=None,
                created_at=datetime.now(timezone.utc),
            ),
            Task(
                id=1,
                chat_id=100,
                text="Завтра",
                deadline=date(2026, 6, 3),
                created_at=datetime.now(timezone.utc),
            ),
        ]

        self.assertEqual(
            build_task_list_text(tasks),
            "02.06.2026\n"
            "#2 Сегодня утром 09:00\n"
            "#3 Сегодня без времени\n\n"
            "03.06.2026\n"
            "#1 Завтра\n\n"
            "Без дедлайна\n"
            "#4 Без дедлайна раньше\n"
            "#5 Без дедлайна позже",
        )

    def test_build_task_hint_callback(self) -> None:
        self.assertEqual(build_task_hint_callback(7), "todo:list:hint:7")

    def test_build_task_done_callback(self) -> None:
        self.assertEqual(build_task_done_callback(7), "todo:list:done:7")

    def test_build_task_page_limits_visible_tasks(self) -> None:
        tasks = [
            Task(
                id=task_id,
                chat_id=100,
                text=f"Задача {task_id}",
                deadline=None,
                created_at=datetime.now(timezone.utc),
            )
            for task_id in range(1, 8)
        ]

        first_page = build_task_page(tasks, page=0)
        second_page = build_task_page(tasks, page=1)

        self.assertEqual([task.id for task in first_page.tasks], [1, 2, 3, 4, 5, 6])
        self.assertEqual(first_page.total_pages, 2)
        self.assertEqual([task.id for task in second_page.tasks], [7])
        self.assertEqual(second_page.page, 1)

    def test_build_task_page_clamps_out_of_range_page(self) -> None:
        tasks = [
            Task(
                id=task_id,
                chat_id=100,
                text=f"Задача {task_id}",
                deadline=None,
                created_at=datetime.now(timezone.utc),
            )
            for task_id in range(1, 8)
        ]

        task_page = build_task_page(tasks, page=99)

        self.assertEqual(task_page.page, 1)
        self.assertEqual([task.id for task in task_page.tasks], [7])

    def test_build_task_page_hint_text_adds_page_number_when_needed(self) -> None:
        self.assertEqual(build_task_page_hint_text(0, 1), "Выбери задачу на этой странице.")
        self.assertEqual(
            build_task_page_hint_text(1, 3),
            "Выбери задачу на этой странице.\nСтраница 2 из 3",
        )

    def test_task_page_callbacks_preserve_list_and_page(self) -> None:
        self.assertEqual(
            build_task_hint_callback(task_id=7, list_id="general", page=1),
            "todo:list:hint:7:1:general",
        )
        self.assertEqual(
            parse_task_hint_context("todo:list:hint:7:1:general"),
            (7, 1, "general"),
        )
        self.assertEqual(
            build_task_page_callback(list_id="general", page=1),
            "todo:list:page:1:general",
        )
        self.assertEqual(
            parse_task_page_callback("todo:list:page:1:general"),
            (1, "general"),
        )
        self.assertEqual(
            build_task_back_callback(list_id="general", page=1),
            "todo:list:back:1:general",
        )
        self.assertEqual(
            parse_task_back_context("todo:list:back:1:general"),
            ("general", 1),
        )

    def test_snooze_callbacks_preserve_list_and_page(self) -> None:
        self.assertEqual(
            build_task_snooze_menu_callback(task_id=7, list_id="shopping", page=0),
            "todo:list:snooze:menu:7:0:shopping",
        )
        self.assertEqual(
            build_task_snoozed_hint_callback(task_id=7, list_id="shopping", page=1),
            "todo:list:snoozed:hint:7:1:shopping",
        )
        self.assertEqual(
            parse_task_snoozed_hint_context("todo:list:snoozed:hint:7:1:shopping"),
            (7, 1, "shopping"),
        )
        self.assertEqual(
            build_task_snoozed_page_callback(list_id="shopping", page=1),
            "todo:list:snoozed:page:1:shopping",
        )
        self.assertEqual(
            parse_task_snoozed_page_callback("todo:list:snoozed:page:1:shopping"),
            (1, "shopping"),
        )
        self.assertEqual(
            build_task_snoozed_back_callback(list_id="shopping", page=1),
            "todo:list:snoozed:back:1:shopping",
        )
        self.assertEqual(
            parse_task_snoozed_back_context("todo:list:snoozed:back:1:shopping"),
            ("shopping", 1),
        )


if __name__ == "__main__":
    unittest.main()
