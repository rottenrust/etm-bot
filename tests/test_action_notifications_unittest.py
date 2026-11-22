import unittest
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from easy_task_manager.action_notifications import (
    build_family_member_joined_notification,
    build_family_member_removed_notification,
    build_task_created_notification,
    send_family_action_notification,
)
from easy_task_manager.family_storage import JsonFamilyStorage
from easy_task_manager.task_storage import Task


class FakeBot:
    def __init__(self) -> None:
        self.messages: list[tuple[int, str]] = []

    async def send_message(self, chat_id: int, text: str) -> None:
        self.messages.append((chat_id, text))


class ActionNotificationTextTests(unittest.TestCase):
    def test_build_task_created_notification_includes_author_and_task(self) -> None:
        task = Task(
            id=1,
            chat_id=100,
            text="Купить молоко",
            deadline=None,
            created_at=datetime.now(timezone.utc),
        )

        self.assertEqual(
            build_task_created_notification("Паша", task),
            "Паша: задача добавлена\nБез дедлайна\n#1 Купить молоко",
        )

    def test_build_family_member_notifications_use_member_name(self) -> None:
        self.assertEqual(
            build_family_member_joined_notification("masha"),
            "masha: присоединился к семейному списку",
        )
        self.assertEqual(
            build_family_member_removed_notification("masha"),
            "masha: удален из семейного списка",
        )


class ActionNotificationDeliveryTests(unittest.IsolatedAsyncioTestCase):
    async def test_send_family_action_notification_sends_to_other_members_only(self) -> None:
        bot = FakeBot()
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = JsonFamilyStorage(Path(temp_dir) / "families.json")
            storage.initialize({100: "Паша", 200: "Маша"})
            sent_count = await send_family_action_notification(
                bot=bot,
                actor_chat_id=100,
                text="Паша: задача добавлена\nБез дедлайна\n#1 Купить молоко",
                storage=storage,
            )

        self.assertEqual(sent_count, 1)
        self.assertEqual(
            bot.messages,
            [(200, "Паша: задача добавлена\nБез дедлайна\n#1 Купить молоко")],
        )

    async def test_removed_legacy_member_gets_no_notifications_after_restart(self) -> None:
        bot = FakeBot()
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = JsonFamilyStorage(Path(temp_dir) / "families.json")
            configured_members = {100: "Паша", 200: "Маша"}
            storage.initialize(configured_members)
            storage.remove_member(family_id="default", chat_id=200)
            storage.initialize(configured_members)

            sent_count = await send_family_action_notification(
                bot=bot,
                actor_chat_id=100,
                family_id="default",
                text="Паша: задача добавлена",
                storage=storage,
            )

        self.assertEqual(sent_count, 0)
        self.assertEqual(bot.messages, [])

    async def test_send_family_action_notification_uses_family_recipients(self) -> None:
        bot = FakeBot()

        with patch(
            "easy_task_manager.action_notifications.family_storage.list_other_family_chat_ids",
            return_value=(200,),
        ) as recipients_mock:
            sent_count = await send_family_action_notification(
                bot=bot,
                actor_chat_id=100,
                family_id="family_a",
                text="Паша: задача добавлена\nБез дедлайна\n#1 Купить молоко",
            )

        recipients_mock.assert_called_once_with(family_id="family_a", actor_chat_id=100)
        self.assertEqual(sent_count, 1)
        self.assertEqual(
            bot.messages,
            [(200, "Паша: задача добавлена\nБез дедлайна\n#1 Купить молоко")],
        )


if __name__ == "__main__":
    unittest.main()
