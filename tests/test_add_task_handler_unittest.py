import unittest
import tempfile
from datetime import date, datetime, time, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from easy_task_manager.add_task_contract import (
    ASK_DEADLINE_TIME_TEXT,
    ASK_RECURRENCE_TEXT,
    ASK_TASK_TEXT,
    CUSTOM_DEADLINE_INVALID_TEXT,
    CUSTOM_DEADLINE_PROMPT_TEXT,
    CUSTOM_DEADLINE_TIME_INVALID_TEXT,
    DEADLINE_ADDED_TEXT,
    DEADLINE_CUSTOM_CALLBACK,
    DEADLINE_SKIPPED_TEXT,
    DEADLINE_SKIP_CALLBACK,
    DEADLINE_TIME_ADDED_TEXT,
    DEADLINE_TIME_SKIP_CALLBACK,
    DEADLINE_TODAY_CALLBACK,
    DEADLINE_TOMORROW_CALLBACK,
    RECURRENCE_MONTHLY_CALLBACK,
    RECURRENCE_SKIP_CALLBACK,
)
from easy_task_manager.handlers.add_task import (
    AddTaskStates,
    _complete_task_creation,
    handle_add_button,
    handle_add_command,
    handle_add_to_list_button,
    handle_task_text,
    handle_custom_deadline,
    handle_deadline_choice,
    handle_deadline_time,
    handle_deadline_time_skip,
    handle_recurrence_choice,
    family_storage as add_family_storage,
    task_list_storage as add_task_list_storage,
    task_storage as add_task_storage,
)
from easy_task_manager.handlers.start import (
    family_storage as start_family_storage,
    task_list_storage as start_task_list_storage,
    task_storage as start_task_storage,
)
from easy_task_manager.action_notifications import family_storage as notification_family_storage
from easy_task_manager.task_lists_contract import ASK_TASK_LIST_TEXT
from easy_task_manager.task_storage import Task


class FakeState:
    def __init__(self, data=None) -> None:
        self._data = data or {}
        self.last_state = None
        self.clear_count = 0

    async def get_data(self):
        return self._data

    async def set_state(self, state):
        self.last_state = state

    async def update_data(self, **kwargs):
        self._data.update(kwargs)

    async def clear(self):
        self.clear_count += 1
        self.last_state = None


class FakeBot:
    def __init__(self) -> None:
        self.messages: list[tuple[int, str]] = []

    async def send_message(self, chat_id: int, text: str) -> None:
        self.messages.append((chat_id, text))


class AddTaskHandlerTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        self.storage_paths = [
            (storage, storage.file_path)
            for storage in (
                add_family_storage,
                start_family_storage,
                add_task_storage,
                start_task_storage,
                add_task_list_storage,
                start_task_list_storage,
                notification_family_storage,
            )
        ]
        family_path = root / "families.json"
        tasks_path = root / "tasks.json"
        lists_path = root / "task_lists.json"
        for storage, path in self.storage_paths:
            if storage in (add_family_storage, start_family_storage, notification_family_storage):
                storage.file_path = family_path
            elif storage in (add_task_storage, start_task_storage):
                storage.file_path = tasks_path
            else:
                storage.file_path = lists_path
        self.family_env = patch.dict(
            "os.environ",
            {"FAMILY_MEMBERS": "10:Паша,42:Паша,200:Маша"},
        )
        self.family_env.start()
        add_family_storage.initialize({10: "Паша", 42: "Паша", 200: "Маша"})
        add_task_storage.initialize()
        add_task_list_storage.initialize()

    def tearDown(self) -> None:
        self.family_env.stop()
        for storage, path in self.storage_paths:
            storage.file_path = path
        self.temp_dir.cleanup()

    async def test_add_button_asks_for_list_when_family_has_multiple_lists(self) -> None:
        message = SimpleNamespace(answer=AsyncMock(), chat=SimpleNamespace(id=10))
        callback = SimpleNamespace(message=message, answer=AsyncMock())
        state = FakeState()
        task_lists = [
            SimpleNamespace(id="general", title="Общий"),
            SimpleNamespace(id="shopping", title="Покупки"),
        ]

        with patch(
            "easy_task_manager.handlers.add_task.task_list_storage.list_task_lists_by_family",
            return_value=task_lists,
        ) as lists_mock:
            await handle_add_button(callback=callback, state=state)

        callback.answer.assert_awaited_once()
        lists_mock.assert_called_once_with(family_id="default")
        self.assertEqual(state.last_state, AddTaskStates.waiting_task_list_choice)
        message.answer.assert_awaited_once()
        self.assertEqual(message.answer.await_args.kwargs["text"], ASK_TASK_LIST_TEXT)
        keyboard = message.answer.await_args.kwargs["reply_markup"].inline_keyboard
        self.assertEqual(keyboard[0][0].text, "Общий")
        self.assertEqual(keyboard[0][0].callback_data, "todo:add:list:general")
        self.assertEqual(keyboard[1][0].text, "Покупки")
        self.assertEqual(keyboard[1][0].callback_data, "todo:add:list:shopping")

    async def test_add_button_single_list_asks_task_text_immediately(self) -> None:
        message = SimpleNamespace(answer=AsyncMock(), chat=SimpleNamespace(id=10))
        callback = SimpleNamespace(message=message, answer=AsyncMock())
        state = FakeState()

        with patch(
            "easy_task_manager.handlers.add_task.task_list_storage.list_task_lists_by_family",
            return_value=[SimpleNamespace(id="general", title="Общий")],
        ):
            await handle_add_button(callback=callback, state=state)

        self.assertEqual(state.last_state, AddTaskStates.waiting_task_text)
        self.assertEqual(state._data["selected_task_list_id"], "general")
        message.answer.assert_awaited_once_with(text=ASK_TASK_TEXT)

    async def test_add_command_starts_same_flow_as_add_button(self) -> None:
        message = SimpleNamespace(answer=AsyncMock(), chat=SimpleNamespace(id=10))
        state = FakeState(data={"task_text": "Старый ввод"})

        with patch(
            "easy_task_manager.handlers.add_task.task_list_storage.list_task_lists_by_family",
            return_value=[SimpleNamespace(id="general", title="Общий")],
        ):
            await handle_add_command(message=message, state=state)

        self.assertEqual(state.clear_count, 1)
        self.assertEqual(state.last_state, AddTaskStates.waiting_task_text)
        self.assertEqual(state._data["selected_task_list_id"], "general")
        message.answer.assert_awaited_once_with(text=ASK_TASK_TEXT)

    async def test_add_to_list_button_saves_selected_list_and_asks_task_text(self) -> None:
        message = SimpleNamespace(answer=AsyncMock(), chat=SimpleNamespace(id=10))
        callback = SimpleNamespace(
            data="todo:add:list:shopping",
            message=message,
            answer=AsyncMock(),
        )
        state = FakeState()

        with patch(
            "easy_task_manager.handlers.add_task.task_list_storage.get_task_list",
            return_value=SimpleNamespace(id="shopping", title="Покупки"),
        ) as get_mock:
            await handle_add_to_list_button(callback=callback, state=state)

        get_mock.assert_called_once_with(family_id="default", list_id="shopping")
        self.assertEqual(state.last_state, AddTaskStates.waiting_task_text)
        self.assertEqual(state._data["selected_task_list_id"], "shopping")
        message.answer.assert_awaited_once_with(text=ASK_TASK_TEXT)

    async def test_cancel_in_task_text_returns_to_start_without_creating_task(self) -> None:
        message = SimpleNamespace(
            text=" Отмена ",
            answer=AsyncMock(),
            chat=SimpleNamespace(id=10),
        )
        state = FakeState()

        with patch(
            "easy_task_manager.handlers.add_task.send_start_message",
            new_callable=AsyncMock,
        ) as start_mock, patch(
            "easy_task_manager.handlers.add_task.task_storage.add_task"
        ) as add_task_mock:
            await handle_task_text(message=message, state=state)

        self.assertEqual(state.clear_count, 1)
        start_mock.assert_awaited_once_with(message=message, source="cancel_text")
        add_task_mock.assert_not_called()

    async def test_complete_creation_returns_to_start_message(self) -> None:
        message = SimpleNamespace(chat=SimpleNamespace(id=42))
        state = FakeState(data={"task_text": "Сделать фото"})
        with patch(
            "easy_task_manager.handlers.add_task.task_list_storage.get_task_list",
            return_value=SimpleNamespace(id="general"),
        ), patch(
            "easy_task_manager.handlers.add_task.task_storage.add_task"
        ) as add_task_mock, patch(
            "easy_task_manager.handlers.add_task.send_start_message",
            new_callable=AsyncMock,
        ) as start_mock:
            await _complete_task_creation(
                message=message,
                state=state,
                task_text="Сделать фото",
                deadline=None,
            )

        add_task_mock.assert_called_once_with(
            chat_id=42,
            text="Сделать фото",
            deadline=None,
            deadline_time=None,
            family_id="default",
            list_id="general",
            recurrence=None,
        )
        start_mock.assert_awaited_once()

    async def test_complete_creation_uses_selected_task_list(self) -> None:
        message = SimpleNamespace(chat=SimpleNamespace(id=42))
        state = FakeState(data={"selected_task_list_id": "shopping"})

        with patch(
            "easy_task_manager.handlers.add_task.task_list_storage.get_task_list",
            return_value=SimpleNamespace(id="shopping"),
        ), patch(
            "easy_task_manager.handlers.add_task.task_storage.add_task"
        ) as add_task_mock, patch(
            "easy_task_manager.handlers.add_task.send_start_message",
            new_callable=AsyncMock,
        ):
            await _complete_task_creation(
                message=message,
                state=state,
                task_text="Купить молоко",
                deadline=None,
            )

        add_task_mock.assert_called_once_with(
            chat_id=42,
            text="Купить молоко",
            deadline=None,
            deadline_time=None,
            family_id="default",
            list_id="shopping",
            recurrence=None,
        )

    async def test_complete_creation_wakes_reminder_scheduler(self) -> None:
        message = SimpleNamespace(chat=SimpleNamespace(id=42))
        state = FakeState(data={"task_text": "Сделать фото"})

        with patch(
            "easy_task_manager.handlers.add_task.task_list_storage.get_task_list",
            return_value=SimpleNamespace(id="general"),
        ), patch(
            "easy_task_manager.handlers.add_task.task_storage.add_task"
        ), patch(
            "easy_task_manager.handlers.add_task.send_start_message",
            new_callable=AsyncMock,
        ), patch(
            "easy_task_manager.handlers.add_task.wake_reminder_scheduler"
        ) as wake_mock:
            await _complete_task_creation(
                message=message,
                state=state,
                task_text="Сделать фото",
                deadline=None,
            )

        wake_mock.assert_called_once_with("task_created")

    async def test_complete_creation_notifies_other_family_member(self) -> None:
        bot = FakeBot()
        message = SimpleNamespace(chat=SimpleNamespace(id=42), bot=bot)
        state = FakeState(data={"task_text": "Сделать фото"})
        task = Task(
            id=1,
            chat_id=42,
            text="Сделать фото",
            deadline=None,
            created_at=datetime.now(timezone.utc),
        )

        family_storages = (
            add_family_storage,
            start_family_storage,
            notification_family_storage,
        )
        previous_paths = [(storage, storage.file_path) for storage in family_storages]
        with tempfile.TemporaryDirectory() as family_dir:
            for storage in family_storages:
                storage.file_path = Path(family_dir) / "families.json"
            add_family_storage.initialize({42: "Паша", 200: "Маша"})
            try:
                with patch(
                    "easy_task_manager.handlers.add_task.task_list_storage.get_task_list",
                    return_value=SimpleNamespace(id="general"),
                ), patch(
                    "easy_task_manager.handlers.add_task.task_storage.add_task",
                    return_value=task,
                ), patch(
                    "easy_task_manager.handlers.add_task.send_start_message",
                    new_callable=AsyncMock,
                ):
                    await _complete_task_creation(
                        message=message,
                        state=state,
                        task_text="Сделать фото",
                        deadline=None,
                    )
            finally:
                for storage, path in previous_paths:
                    storage.file_path = path

        self.assertEqual(
            bot.messages,
            [(200, "Паша: задача добавлена\nБез дедлайна\n#1 Сделать фото")],
        )

    async def test_today_branch_asks_for_deadline_time(self) -> None:
        message = SimpleNamespace(answer=AsyncMock(), chat=SimpleNamespace(id=10))
        callback = SimpleNamespace(data=DEADLINE_TODAY_CALLBACK, message=message, answer=AsyncMock())
        state = FakeState(data={"task_text": "Купить хлеб"})

        with patch(
            "easy_task_manager.handlers.add_task._complete_task_creation",
            new_callable=AsyncMock,
        ) as complete_mock, patch(
            "easy_task_manager.handlers.add_task.get_today_moscow",
            return_value=date(2026, 6, 1),
        ):
            await handle_deadline_choice(callback=callback, state=state)

        callback.answer.assert_awaited_once()
        self.assertEqual(state.last_state, AddTaskStates.waiting_deadline_time)
        self.assertEqual(state._data["pending_deadline"], "2026-06-01")
        self.assertEqual(message.answer.await_args.kwargs["text"], ASK_DEADLINE_TIME_TEXT)
        complete_mock.assert_not_called()

    async def test_tomorrow_branch_asks_for_deadline_time(self) -> None:
        message = SimpleNamespace(answer=AsyncMock(), chat=SimpleNamespace(id=10))
        callback = SimpleNamespace(
            data=DEADLINE_TOMORROW_CALLBACK,
            message=message,
            answer=AsyncMock(),
        )
        state = FakeState(data={"task_text": "Позвонить маме"})

        with patch(
            "easy_task_manager.handlers.add_task._complete_task_creation",
            new_callable=AsyncMock,
        ) as complete_mock, patch(
            "easy_task_manager.handlers.add_task.get_tomorrow_moscow",
            return_value=date(2026, 6, 2),
        ):
            await handle_deadline_choice(callback=callback, state=state)

        self.assertEqual(state.last_state, AddTaskStates.waiting_deadline_time)
        self.assertEqual(state._data["pending_deadline"], "2026-06-02")
        self.assertEqual(message.answer.await_args.kwargs["text"], ASK_DEADLINE_TIME_TEXT)
        complete_mock.assert_not_called()

    async def test_skip_branch_creates_without_deadline(self) -> None:
        message = SimpleNamespace(answer=AsyncMock(), chat=SimpleNamespace(id=10))
        callback = SimpleNamespace(data=DEADLINE_SKIP_CALLBACK, message=message, answer=AsyncMock())
        state = FakeState(data={"task_text": "Проверить счета"})

        with patch(
            "easy_task_manager.handlers.add_task._complete_task_creation",
            new_callable=AsyncMock,
        ) as complete_mock:
            await handle_deadline_choice(callback=callback, state=state)

        message.answer.assert_awaited_once_with(text=DEADLINE_SKIPPED_TEXT)
        complete_mock.assert_awaited_once_with(
            message=message,
            state=state,
            task_text="Проверить счета",
            deadline=None,
        )

    async def test_custom_branch_switches_to_custom_date_state(self) -> None:
        message = SimpleNamespace(answer=AsyncMock(), chat=SimpleNamespace(id=10))
        callback = SimpleNamespace(data=DEADLINE_CUSTOM_CALLBACK, message=message, answer=AsyncMock())
        state = FakeState(data={"task_text": "Записаться к врачу"})

        with patch(
            "easy_task_manager.handlers.add_task._complete_task_creation",
            new_callable=AsyncMock,
        ) as complete_mock:
            await handle_deadline_choice(callback=callback, state=state)

        self.assertEqual(state.last_state, AddTaskStates.waiting_custom_deadline)
        message.answer.assert_awaited_once_with(text=CUSTOM_DEADLINE_PROMPT_TEXT)
        complete_mock.assert_not_called()

    async def test_custom_deadline_success_asks_for_deadline_time(self) -> None:
        message = SimpleNamespace(text="31.12.2099", answer=AsyncMock(), chat=SimpleNamespace(id=10))
        state = FakeState(data={"task_text": "Записаться к врачу"})

        with patch(
            "easy_task_manager.handlers.add_task._complete_task_creation",
            new_callable=AsyncMock,
        ) as complete_mock:
            await handle_custom_deadline(message=message, state=state)

        self.assertEqual(state.last_state, AddTaskStates.waiting_deadline_time)
        self.assertEqual(state._data["pending_deadline"], "2099-12-31")
        self.assertEqual(message.answer.await_args.kwargs["text"], ASK_DEADLINE_TIME_TEXT)
        complete_mock.assert_not_called()

    async def test_custom_deadline_invalid_asks_to_repeat_without_clearing_state(self) -> None:
        message = SimpleNamespace(text="завтра", answer=AsyncMock(), chat=SimpleNamespace(id=10))
        state = FakeState(data={"task_text": "Записаться к врачу"})

        with patch(
            "easy_task_manager.handlers.add_task._complete_task_creation",
            new_callable=AsyncMock,
        ) as complete_mock:
            await handle_custom_deadline(message=message, state=state)

        message.answer.assert_awaited_once_with(text=CUSTOM_DEADLINE_INVALID_TEXT)
        self.assertEqual(state.clear_count, 0)
        complete_mock.assert_not_called()

    async def test_cancel_in_custom_deadline_returns_to_start_without_creating_task(self) -> None:
        message = SimpleNamespace(text="отмена", answer=AsyncMock(), chat=SimpleNamespace(id=10))
        state = FakeState(data={"task_text": "Записаться к врачу"})

        with patch(
            "easy_task_manager.handlers.add_task.send_start_message",
            new_callable=AsyncMock,
        ) as start_mock, patch(
            "easy_task_manager.handlers.add_task._complete_task_creation",
            new_callable=AsyncMock,
        ) as complete_mock:
            await handle_custom_deadline(message=message, state=state)

        self.assertEqual(state.clear_count, 1)
        start_mock.assert_awaited_once_with(message=message, source="cancel_text")
        complete_mock.assert_not_called()

    async def test_deadline_time_skip_asks_for_recurrence(self) -> None:
        message = SimpleNamespace(answer=AsyncMock(), chat=SimpleNamespace(id=10))
        callback = SimpleNamespace(
            data=DEADLINE_TIME_SKIP_CALLBACK,
            message=message,
            answer=AsyncMock(),
        )
        state = FakeState(
            data={"task_text": "Записаться к врачу", "pending_deadline": "2099-12-31"}
        )

        with patch(
            "easy_task_manager.handlers.add_task._complete_task_creation",
            new_callable=AsyncMock,
        ) as complete_mock:
            await handle_deadline_time_skip(callback=callback, state=state)

        self.assertEqual(message.answer.await_args_list[0].kwargs["text"], DEADLINE_ADDED_TEXT)
        self.assertEqual(state.last_state, AddTaskStates.waiting_recurrence_choice)
        self.assertEqual(state._data["pending_deadline"], "2099-12-31")
        self.assertIsNone(state._data["pending_deadline_time"])
        self.assertEqual(message.answer.await_args_list[1].kwargs["text"], ASK_RECURRENCE_TEXT)
        complete_mock.assert_not_called()

    async def test_deadline_time_success_asks_for_recurrence(self) -> None:
        message = SimpleNamespace(text="18:30", answer=AsyncMock(), chat=SimpleNamespace(id=10))
        state = FakeState(
            data={"task_text": "Записаться к врачу", "pending_deadline": "2099-12-31"}
        )

        with patch(
            "easy_task_manager.handlers.add_task._complete_task_creation",
            new_callable=AsyncMock,
        ) as complete_mock:
            await handle_deadline_time(message=message, state=state)

        self.assertEqual(message.answer.await_args_list[0].kwargs["text"], DEADLINE_TIME_ADDED_TEXT)
        self.assertEqual(state.last_state, AddTaskStates.waiting_recurrence_choice)
        self.assertEqual(state._data["pending_deadline"], "2099-12-31")
        self.assertEqual(state._data["pending_deadline_time"], "18:30")
        self.assertEqual(message.answer.await_args_list[1].kwargs["text"], ASK_RECURRENCE_TEXT)
        complete_mock.assert_not_called()

    async def test_recurrence_choice_creates_recurring_task(self) -> None:
        message = SimpleNamespace(answer=AsyncMock(), chat=SimpleNamespace(id=10))
        callback = SimpleNamespace(
            data=RECURRENCE_MONTHLY_CALLBACK,
            message=message,
            answer=AsyncMock(),
        )
        state = FakeState(
            data={
                "task_text": "Оплатить интернет",
                "pending_deadline": "2099-12-31",
                "pending_deadline_time": "18:30",
            }
        )

        with patch(
            "easy_task_manager.handlers.add_task._complete_task_creation",
            new_callable=AsyncMock,
        ) as complete_mock:
            await handle_recurrence_choice(callback=callback, state=state)

        complete_mock.assert_awaited_once_with(
            message=message,
            state=state,
            task_text="Оплатить интернет",
            deadline=date(2099, 12, 31),
            deadline_time=time(18, 30),
            recurrence="monthly",
        )

    async def test_recurrence_skip_creates_non_recurring_task(self) -> None:
        message = SimpleNamespace(answer=AsyncMock(), chat=SimpleNamespace(id=10))
        callback = SimpleNamespace(
            data=RECURRENCE_SKIP_CALLBACK,
            message=message,
            answer=AsyncMock(),
        )
        state = FakeState(
            data={"task_text": "Оплатить интернет", "pending_deadline": "2099-12-31"}
        )

        with patch(
            "easy_task_manager.handlers.add_task._complete_task_creation",
            new_callable=AsyncMock,
        ) as complete_mock:
            await handle_recurrence_choice(callback=callback, state=state)

        complete_mock.assert_awaited_once_with(
            message=message,
            state=state,
            task_text="Оплатить интернет",
            deadline=date(2099, 12, 31),
            deadline_time=None,
            recurrence=None,
        )

    async def test_deadline_time_invalid_asks_to_repeat_without_clearing_state(self) -> None:
        message = SimpleNamespace(text="вечером", answer=AsyncMock(), chat=SimpleNamespace(id=10))
        state = FakeState(
            data={"task_text": "Записаться к врачу", "pending_deadline": "2099-12-31"}
        )

        with patch(
            "easy_task_manager.handlers.add_task._complete_task_creation",
            new_callable=AsyncMock,
        ) as complete_mock:
            await handle_deadline_time(message=message, state=state)

        message.answer.assert_awaited_once_with(text=CUSTOM_DEADLINE_TIME_INVALID_TEXT)
        self.assertEqual(state.clear_count, 0)
        complete_mock.assert_not_called()

    async def test_cancel_in_deadline_time_returns_to_start_without_creating_task(self) -> None:
        message = SimpleNamespace(text="ОТМЕНА", answer=AsyncMock(), chat=SimpleNamespace(id=10))
        state = FakeState(
            data={"task_text": "Записаться к врачу", "pending_deadline": "2099-12-31"}
        )

        with patch(
            "easy_task_manager.handlers.add_task.send_start_message",
            new_callable=AsyncMock,
        ) as start_mock, patch(
            "easy_task_manager.handlers.add_task._complete_task_creation",
            new_callable=AsyncMock,
        ) as complete_mock:
            await handle_deadline_time(message=message, state=state)

        self.assertEqual(state.clear_count, 1)
        start_mock.assert_awaited_once_with(message=message, source="cancel_text")
        complete_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
