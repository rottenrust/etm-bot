import hashlib
import hmac
import json
import tempfile
import time
import unittest
from pathlib import Path
from datetime import date, datetime, time as clock_time, timedelta
from urllib.parse import urlencode

from aiohttp.test_utils import TestClient, TestServer

from easy_task_manager.deadline_utils import MOSCOW_TIMEZONE, get_today_moscow
from easy_task_manager.family_storage import JsonFamilyStorage
from easy_task_manager.reminder_state_storage import JsonReminderStateStorage
from easy_task_manager.reminders import (
    family_storage as reminders_family_storage,
    run_due_task_reminder_scheduler,
    task_list_storage as reminders_task_list_storage,
)
from easy_task_manager.server import create_app
from easy_task_manager.task_list_storage import JsonTaskListStorage
from easy_task_manager.task_storage import JsonTaskStorage


TOKEN = "123456:synthetic-mini-app-test-token"


class StopScheduler(Exception):
    pass


class FakeBot:
    def __init__(self) -> None:
        self.messages: list[tuple[int, str]] = []

    async def send_message(
        self,
        chat_id: int,
        text: str,
        reply_markup: object = None,
    ) -> None:
        self.messages.append((chat_id, text))

    async def get_me(self):
        return type("BotIdentity", (), {"username": "test_task_bot"})()


class MiniAppApiTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        self.tasks = JsonTaskStorage(root / "tasks.json")
        self.lists = JsonTaskListStorage(root / "task_lists.json")
        self.families = JsonFamilyStorage(root / "families.json")
        self.families.initialize({101: "Паша", 102: "Маша"})
        self.other_member = self.families.create_family_for_member(201, "Ира")
        self.bot = FakeBot()
        static_dir = root / "dist"
        (static_dir / "assets").mkdir(parents=True)
        (static_dir / "assets" / "app.js").write_text("console.log('mini app');", encoding="utf-8")
        (static_dir / "index.html").write_text("<!doctype html><div id='app'></div>", encoding="utf-8")
        app = create_app(
            task_storage=self.tasks,
            task_list_storage=self.lists,
            family_storage=self.families,
            bot=self.bot,
            bot_token=TOKEN,
            static_dir=static_dir,
        )
        self.client = TestClient(TestServer(app))
        await self.client.start_server()

    async def asyncTearDown(self) -> None:
        await self.client.close()
        self.temp_dir.cleanup()

    async def test_health_requires_no_auth_and_unknown_api_is_json_404(self) -> None:
        response = await self.client.get("/healthz")
        self.assertEqual(response.status, 200)
        self.assertEqual(await response.json(), {"status": "ok"})

        response = await self.client.get("/api/unknown")
        self.assertEqual(response.status, 404)
        self.assertEqual((await response.json())["error"], "API endpoint not found")

        response = await self.client.get("/api")
        self.assertEqual(response.status, 404)
        self.assertEqual(response.content_type, "application/json")
        self.assertEqual((await response.json())["error"], "API endpoint not found")

        response = await self.client.get("/assets/app.js")
        self.assertEqual(response.status, 200)
        self.assertEqual(await response.text(), "console.log('mini app');")

        response = await self.client.get("/assets/noext")
        self.assertEqual(response.status, 404)
        self.assertNotEqual(response.content_type, "text/html")

        response = await self.client.get("/help")
        self.assertEqual(response.status, 200)
        self.assertIn("<div id='app'></div>", await response.text())

    async def test_api_rejects_bad_init_data_as_json_401(self) -> None:
        response = await self.client.get(
            "/api/me",
            headers={"X-Telegram-Init-Data": "hash=%D0%B0&auth_date=1&user=%7B%7D"},
        )

        self.assertEqual(response.status, 401)
        self.assertIn("error", await response.json())

    async def test_two_members_share_crud_but_other_family_cannot_access_task(self) -> None:
        deadline = get_today_moscow()
        response = await self.request(
            "POST",
            "/api/tasks",
            101,
            json={
                "text": "Купить молоко",
                "deadline": deadline.isoformat(),
                "deadlineTime": "18:00",
                "listId": "general",
                "note": "2 литра",
                "reminderEnabled": False,
            },
        )
        self.assertEqual(response.status, 201)
        task = (await response.json())["task"]
        task_id = task["id"]

        response = await self.request("GET", "/api/lists", 102)
        data = await response.json()
        self.assertIn(task_id, [item["id"] for category in data["categories"] for item in category["tasks"]])

        response = await self.request(
            "PATCH",
            f"/api/tasks/{task_id}",
            201,
            json={"text": "Чужое изменение", "deadline": None, "listId": "general"},
        )
        self.assertEqual(response.status, 404)

        self.lists.create_task_list_from_preset("default", "health")
        self.bot.messages.clear()
        updated_deadline = deadline + timedelta(days=2)
        response = await self.request(
            "PATCH",
            f"/api/tasks/{task_id}",
            102,
            json={
                "text": "Купить молоко и хлеб",
                "deadline": updated_deadline.isoformat(),
                "deadlineTime": "19:15",
                "listId": "health",
                "note": "Молоко 2 литра, хлеб цельнозерновой",
                "reminderEnabled": True,
            },
        )
        self.assertEqual(response.status, 200)
        updated_task = (await response.json())["task"]
        self.assertEqual(
            {key: updated_task[key] for key in ("text", "deadline", "deadlineTime", "listId", "note", "reminderEnabled")},
            {
                "text": "Купить молоко и хлеб",
                "deadline": updated_deadline.isoformat(),
                "deadlineTime": "19:15",
                "listId": "health",
                "note": "Молоко 2 литра, хлеб цельнозерновой",
                "reminderEnabled": True,
            },
        )

        response = await self.request("GET", "/api/lists", 101)
        lists_for_first_member = await response.json()
        health_tasks = next(
            category["tasks"]
            for category in lists_for_first_member["categories"]
            if category["id"] == "health"
        )
        saved_task = next(item for item in health_tasks if item["id"] == task_id)
        self.assertEqual(saved_task, updated_task)
        self.assertEqual(len(self.bot.messages), 1)
        self.assertEqual(self.bot.messages[0][0], 101)
        self.assertIn("Маша: задача изменена", self.bot.messages[0][1])
        self.assertIn("Купить молоко и хлеб", self.bot.messages[0][1])

        response = await self.request(
            "POST",
            "/api/tasks",
            101,
            json={"text": "Чужой список", "listId": "not-enabled"},
        )
        self.assertEqual(response.status, 404)

        response = await self.request("DELETE", f"/api/tasks/{task_id}", 101)
        self.assertEqual(response.status, 200)
        self.assertTrue((await response.json())["deleted"])
        self.assertEqual(len(self.bot.messages), 2)
        self.assertEqual(self.bot.messages[1][0], 102)

    async def test_repeated_completion_creates_one_recurring_successor_and_notice(self) -> None:
        today = get_today_moscow()
        task = self.tasks.add_task(
            chat_id=101,
            family_id="default",
            text="Полить цветы",
            deadline=today,
            recurrence="daily",
            reminder_enabled=False,
        )

        first = await self.request("POST", f"/api/tasks/{task.id}/complete", 101, json={})
        second = await self.request("POST", f"/api/tasks/{task.id}/complete", 102, json={})

        self.assertEqual(first.status, 200)
        self.assertEqual(second.status, 200)
        family_tasks = self.tasks.list_tasks_by_family("default", include_completed=True)
        self.assertEqual(len([item for item in family_tasks if item.text == "Полить цветы"]), 2)
        self.assertEqual(len(self.bot.messages), 1)
        self.assertTrue(any(item.completed_at is not None for item in family_tasks))
        self.assertTrue(any(item.completed_at is None for item in family_tasks))

    async def test_completed_overdue_stays_visible_while_active_counts_drop(self) -> None:
        today = get_today_moscow()
        overdue = self.tasks.add_task(
            chat_id=101,
            family_id="default",
            text="Просроченное",
            deadline=today - timedelta(days=1),
            reminder_enabled=False,
        )
        self.tasks.complete_task_once_by_family("default", overdue.id)
        today_task = self.tasks.add_task(
            chat_id=102,
            family_id="default",
            text="На сегодня",
            deadline=today,
            reminder_enabled=False,
        )
        no_deadline = self.tasks.add_task(
            chat_id=102,
            family_id="default",
            text="Без даты",
            deadline=None,
            reminder_enabled=False,
        )

        response = await self.request("GET", "/api/home", 101)
        home = await response.json()
        sections = {section["id"]: section for section in home["sections"]}
        by_id = {
            task["id"]: task
            for section in home["sections"]
            for task in section["tasks"]
        }

        self.assertIsNotNone(by_id[overdue.id]["completedAt"])
        self.assertEqual(sections["overdue"]["tasks"][0]["id"], overdue.id)
        self.assertIsNone(by_id[today_task.id]["completedAt"])
        self.assertIsNone(by_id[no_deadline.id]["completedAt"])
        self.assertEqual(home["stats"], {"today": 1, "overdue": 0})

        response = await self.request(
            "GET",
            f"/api/home?mode=calendar&date={today.isoformat()}",
            101,
        )
        calendar = {day["date"]: day for day in (await response.json())["calendar"]}
        self.assertTrue(calendar[today.isoformat()]["hasTasks"])
        self.assertFalse(calendar[(today + timedelta(days=1)).isoformat()]["hasTasks"])

        selected_tomorrow = today + timedelta(days=1)
        response = await self.request(
            "GET",
            f"/api/home?mode=calendar&date={selected_tomorrow.isoformat()}",
            101,
        )
        titles = [section["title"] for section in (await response.json())["sections"]]
        self.assertEqual(titles[:3], ["Просрочено", "Сегодня", "Завтра"])

        selected_later = today + timedelta(days=60)
        self.tasks.add_task(
            chat_id=101,
            family_id="default",
            text="Дело через две недели",
            deadline=selected_later,
            reminder_enabled=False,
        )
        response = await self.request(
            "GET",
            f"/api/home?mode=calendar&date={selected_later.isoformat()}",
            101,
        )
        later_home = await response.json()
        calendar = {day["date"]: day for day in later_home["calendar"]}
        self.assertEqual(len(calendar), 31)
        self.assertTrue(calendar[selected_later.isoformat()]["selected"])
        self.assertTrue(calendar[selected_later.isoformat()]["hasTasks"])
        self.assertEqual(
            min(date.fromisoformat(day) for day in calendar),
            selected_later - timedelta(days=15),
        )

        response = await self.request(
            "GET",
            f"/api/home?mode=calendar&date={date.max.isoformat()}",
            101,
        )
        self.assertEqual(response.status, 400)

    async def test_api_reminders_survive_scheduler_restart_without_duplicates(self) -> None:
        deadline = get_today_moscow().isoformat()
        created: dict[str, dict[str, object]] = {}
        for name, reminder_enabled in (("включено", True), ("выключено", False), ("завершено", True)):
            response = await self.request(
                "POST",
                "/api/tasks",
                101,
                json={
                    "text": f"Напоминание {name}",
                    "deadline": deadline,
                    "deadlineTime": "18:59",
                    "listId": "general",
                    "reminderEnabled": reminder_enabled,
                },
            )
            self.assertEqual(response.status, 201)
            created[name] = (await response.json())["task"]

        response = await self.request(
            "POST",
            f"/api/tasks/{created['завершено']['id']}/complete",
            102,
        )
        self.assertEqual(response.status, 200)
        self.bot.messages.clear()

        state_path = Path(self.temp_dir.name) / "reminder_state.json"
        now = datetime.combine(get_today_moscow(), clock_time(19, 1), tzinfo=MOSCOW_TIMEZONE)
        previous_paths = (
            (reminders_family_storage, reminders_family_storage.file_path),
            (reminders_task_list_storage, reminders_task_list_storage.file_path),
        )
        reminders_family_storage.file_path = self.families.file_path
        reminders_task_list_storage.file_path = self.lists.file_path

        state = JsonReminderStateStorage(state_path)
        state.initialize()
        state.mark_daily_slot_processed(now.date(), "morning", now)
        state.mark_daily_slot_processed(now.date(), "evening", now)

        async def stop_after_due(wait_seconds: float) -> None:
            if wait_seconds > 0:
                raise StopScheduler

        try:
            for restart in range(2):
                fresh_tasks = JsonTaskStorage(self.tasks.file_path)
                reminder_state = JsonReminderStateStorage(state_path)
                reminder_state.initialize()
                with self.assertRaises(StopScheduler):
                    await run_due_task_reminder_scheduler(
                        bot=self.bot,
                        storage=fresh_tasks,
                        reminder_state=reminder_state,
                        sleep=stop_after_due,
                        now_provider=lambda: now,
                    )
                if restart == 0:
                    self.assertEqual(len(self.bot.messages), 2)
                    self.assertEqual({chat_id for chat_id, _ in self.bot.messages}, {101, 102})
                    self.assertTrue(all("включено" in text for _, text in self.bot.messages))
                    self.assertTrue(all("выключено" not in text for _, text in self.bot.messages))
                    self.assertTrue(all("завершено" not in text for _, text in self.bot.messages))
        finally:
            for storage, path in previous_paths:
                storage.file_path = path

        self.assertEqual(len(self.bot.messages), 2)

    async def test_removed_member_loses_api_access_and_restart_does_not_restore_it(self) -> None:
        response = await self.request("DELETE", "/api/family/members/102", 101)
        self.assertEqual(response.status, 200)
        self.families.initialize({101: "Паша", 102: "Маша"})
        self.assertEqual(len(self.bot.messages), 1)
        self.assertEqual(self.bot.messages[0][0], 102)
        self.assertIn("Маша", self.bot.messages[0][1])

        response = await self.request("GET", "/api/me", 102)
        self.assertEqual(response.status, 200)
        self.assertFalse((await response.json())["hasFamily"])

        response = await self.request("GET", "/api/home", 102)
        self.assertEqual(response.status, 403)

    async def test_only_owner_can_remove_family_member_and_owner_cannot_remove_self(self) -> None:
        response = await self.request("DELETE", "/api/family/members/101", 101)
        self.assertEqual(response.status, 403)
        response = await self.request("DELETE", "/api/family/members/201", 102)
        self.assertEqual(response.status, 403)
        self.assertEqual(self.families.get_family_id_for_chat(201), self.other_member.family_id)

    async def test_invite_is_for_bot_start_and_new_user_has_no_auto_family(self) -> None:
        response = await self.request("POST", "/api/family/invite", 101, json={})
        self.assertEqual(response.status, 200)
        invitation = await response.json()
        self.assertIn("start=", invitation["botLink"])

        response = await self.request("GET", "/api/me", 301)
        self.assertEqual(response.status, 200)
        self.assertFalse((await response.json())["hasFamily"])
        status, member = self.families.join_family_by_invite(301, "Новый", invitation["code"])
        self.assertEqual(status, "success")
        self.assertEqual(member.family_id, "default")

    async def request(self, method: str, path: str, chat_id: int, **kwargs):
        headers = dict(kwargs.pop("headers", {}))
        headers["X-Telegram-Init-Data"] = signed_init_data(chat_id)
        return await self.client.request(method, path, headers=headers, **kwargs)


def signed_init_data(chat_id: int) -> str:
    fields = {
        "auth_date": str(int(time.time())),
        "user": json.dumps(
            {"id": chat_id, "first_name": f"User {chat_id}"},
            separators=(",", ":"),
        ),
    }
    check_string = "\n".join(f"{key}={fields[key]}" for key in sorted(fields))
    secret = hmac.new(b"WebAppData", TOKEN.encode(), hashlib.sha256).digest()
    fields["hash"] = hmac.new(secret, check_string.encode(), hashlib.sha256).hexdigest()
    return urlencode(fields)


if __name__ == "__main__":
    unittest.main()
