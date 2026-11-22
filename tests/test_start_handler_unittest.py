import unittest
import tempfile
from datetime import date, datetime, time, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import ANY, AsyncMock, patch

from easy_task_manager.add_task_contract import (
    ASK_DEADLINE_TIME_TEXT,
    CUSTOM_DEADLINE_INVALID_TEXT,
    CUSTOM_DEADLINE_PROMPT_TEXT,
    CUSTOM_DEADLINE_TIME_INVALID_TEXT,
    DEADLINE_ADDED_TEXT,
    DEADLINE_SKIPPED_TEXT,
    DEADLINE_TIME_ADDED_TEXT,
    DEADLINE_TIME_SKIP_CALLBACK,
)
from easy_task_manager.handlers.start import (
    FamilyOnboardingStates,
    SelectedTaskDeadlineStates,
    handle_back_to_start_callback,
    handle_cancel_delete_family_callback,
    handle_confirm_delete_family_callback,
    handle_create_family_callback,
    handle_delete_family_callback,
    handle_family_menu_callback,
    handle_family_members_callback,
    handle_remove_family_member_callback,
    handle_cancel_remove_family_member_callback,
    handle_confirm_remove_family_member_callback,
    handle_invite_callback,
    handle_join_family_callback,
    handle_join_family_code,
    handle_family_command,
    handle_help_command,
    handle_lists_command,
    handle_manual_start,
    handle_menu_command,
    handle_selected_task_custom_deadline,
    handle_selected_task_deadline_time,
    handle_selected_task_deadline_time_skip,
    handle_list_callback,
    handle_task_list_create_callback,
    handle_task_list_open_callback,
    handle_task_change_list_callback,
    handle_task_move_to_list_callback,
    handle_task_lists_add_callback,
    handle_task_lists_callback,
    handle_task_deadline_custom_callback,
    handle_task_deadline_menu_callback,
    handle_task_deadline_remove_callback,
    handle_task_deadline_today_callback,
    handle_task_recurrence_monthly_callback,
    handle_task_recurrence_remove_callback,
    handle_task_back_callback,
    handle_task_done_callback,
    handle_task_hint_callback,
    handle_task_page_callback,
    send_start_message,
    _get_family_id_for_chat,
    family_storage,
    task_list_storage as start_task_list_storage,
    task_storage as start_task_storage,
)
from easy_task_manager.handlers.add_task import (
    family_storage as add_family_storage,
    task_list_storage as add_task_list_storage,
    task_storage as add_task_storage,
)
from easy_task_manager.action_notifications import family_storage as notification_family_storage
from easy_task_manager.list_tasks_contract import (
    LIST_EMPTY_TEXT,
    LIST_HINTS_TEXT,
    TASK_DONE_TEXT,
    TASK_RECURRENCE_REMOVED_TEXT,
    TASK_RECURRENCE_UPDATED_TEMPLATE,
)
from easy_task_manager.start_contract import (
    ADD_TASK_CALLBACK_DATA,
    FAMILY_DELETED_TEXT,
    FAMILY_DELETE_CANCELLED_TEXT,
    FAMILY_DELETE_CONFIRM_TEXT,
    FAMILY_CREATED_TEXT,
    FAMILY_MEMBER_REMOVE_FORBIDDEN_TEXT,
    FAMILY_MEMBER_REMOVED_TEXT_TEMPLATE,
    FAMILY_MEMBERS_TEXT,
    FAMILY_MENU_TEXT,
    HELP_TEXT,
    INVITE_TEXT_TEMPLATE,
    JOIN_FAMILY_PROMPT_TEXT,
    JOIN_FAMILY_SUCCESS_TEXT,
    NEW_USER_TEXT,
    WELCOME_TEXT,
)
from easy_task_manager.task_lists_contract import (
    TASK_LIST_CREATED_TEMPLATE,
    TASK_LIST_CHANGED_TEMPLATE,
    CHANGE_TASK_LIST_TEXT,
    TASK_LISTS_ADD_TEXT,
    TASK_LISTS_TEXT,
)
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


class StartHandlerTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        self.storage_paths = [
            (storage, storage.file_path)
            for storage in (
                family_storage,
                add_family_storage,
                start_task_storage,
                add_task_storage,
                start_task_list_storage,
                add_task_list_storage,
                notification_family_storage,
            )
        ]
        family_path = root / "families.json"
        tasks_path = root / "tasks.json"
        lists_path = root / "task_lists.json"
        for storage, path in self.storage_paths:
            if storage in (family_storage, add_family_storage, notification_family_storage):
                storage.file_path = family_path
            elif storage in (start_task_storage, add_task_storage):
                storage.file_path = tasks_path
            else:
                storage.file_path = lists_path
        self.family_env = patch.dict(
            "os.environ",
            {"FAMILY_MEMBERS": "200:Паша,201:Маша"},
        )
        self.family_env.start()
        family_storage.initialize({200: "Паша", 201: "Маша"})
        start_task_storage.initialize()
        start_task_list_storage.initialize()

    def tearDown(self) -> None:
        self.family_env.stop()
        for storage, path in self.storage_paths:
            storage.file_path = path
        self.temp_dir.cleanup()

    async def test_send_start_message_uses_start_keyboard(self) -> None:
        message = SimpleNamespace(
            from_user=SimpleNamespace(id=100),
            chat=SimpleNamespace(id=200),
            answer=AsyncMock(),
        )

        await send_start_message(message=message, source="test")

        message.answer.assert_awaited_once()
        kwargs = message.answer.await_args.kwargs
        self.assertEqual(kwargs["text"], WELCOME_TEXT)
        self.assertEqual(len(kwargs["reply_markup"].inline_keyboard), 2)
        self.assertEqual(len(kwargs["reply_markup"].inline_keyboard[0]), 2)
        self.assertEqual(kwargs["reply_markup"].inline_keyboard[0][0].text, "Добавить")
        self.assertEqual(kwargs["reply_markup"].inline_keyboard[0][1].text, "Списки")
        self.assertEqual(kwargs["reply_markup"].inline_keyboard[1][0].text, "Семья")

    async def test_send_start_message_adds_mini_app_for_existing_member(self) -> None:
        message = SimpleNamespace(
            from_user=SimpleNamespace(id=100),
            chat=SimpleNamespace(id=200),
            answer=AsyncMock(),
        )

        with patch.dict("os.environ", {"WEBAPP_URL": "https://kotik.pavelmarchik.ru"}):
            await send_start_message(message=message, source="test")

        keyboard = message.answer.await_args.kwargs["reply_markup"]
        mini_app_button = keyboard.inline_keyboard[-1][0]
        self.assertEqual(mini_app_button.text, "Открыть мини-приложение")
        self.assertEqual(mini_app_button.web_app.url, "https://kotik.pavelmarchik.ru")

    async def test_send_start_message_asks_new_user_to_choose_family_flow(self) -> None:
        message = SimpleNamespace(
            from_user=SimpleNamespace(id=100, full_name="Новый пользователь"),
            chat=SimpleNamespace(id=300),
            text="/start",
            answer=AsyncMock(),
        )

        with patch(
            "easy_task_manager.handlers.start.family_storage.get_family_id_for_chat",
            return_value=None,
        ):
            await send_start_message(message=message, source="test")

        message.answer.assert_awaited_once()
        kwargs = message.answer.await_args.kwargs
        self.assertEqual(kwargs["text"], NEW_USER_TEXT)
        keyboard = kwargs["reply_markup"].inline_keyboard
        self.assertEqual(keyboard[0][0].text, "Присоединиться")
        self.assertEqual(keyboard[0][1].text, "Создать семью")

    async def test_removed_legacy_member_cannot_reenter_bot_after_restart(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            old_path = family_storage.file_path
            try:
                family_storage.file_path = Path(temp_dir) / "families.json"
                configured_members = {200: "Паша", 201: "Маша"}
                family_storage.initialize(configured_members)
                family_storage.remove_member(family_id="default", chat_id=201)
                family_storage.initialize(configured_members)

                self.assertIsNone(_get_family_id_for_chat(201))
            finally:
                family_storage.file_path = old_path

    async def test_manual_cancel_clears_state_and_shows_start(self) -> None:
        message = SimpleNamespace(
            from_user=SimpleNamespace(id=100),
            chat=SimpleNamespace(id=200),
            text=" отмена ",
            answer=AsyncMock(),
        )
        state = FakeState(data={"task_text": "Купить молоко"})

        await handle_manual_start(message=message, state=state)

        self.assertEqual(state.clear_count, 1)
        message.answer.assert_awaited_once()
        self.assertEqual(message.answer.await_args.kwargs["text"], WELCOME_TEXT)

    async def test_unexpected_text_does_not_clear_state_or_show_start(self) -> None:
        message = SimpleNamespace(
            chat=SimpleNamespace(id=200),
            text="привет",
            answer=AsyncMock(),
        )
        state = FakeState(data={"task_text": "Купить молоко"})

        await handle_manual_start(message=message, state=state)

        self.assertEqual(state.clear_count, 0)
        message.answer.assert_not_awaited()

    async def test_menu_command_clears_state_and_shows_start(self) -> None:
        message = SimpleNamespace(
            from_user=SimpleNamespace(id=100),
            chat=SimpleNamespace(id=200),
            text="/menu",
            answer=AsyncMock(),
        )
        state = FakeState(data={"task_text": "Купить молоко"})

        await handle_menu_command(message=message, state=state)

        self.assertEqual(state.clear_count, 1)
        message.answer.assert_awaited_once()
        self.assertEqual(message.answer.await_args.kwargs["text"], WELCOME_TEXT)

    async def test_lists_command_opens_task_lists(self) -> None:
        message = SimpleNamespace(chat=SimpleNamespace(id=200), answer=AsyncMock())
        state = FakeState()

        with patch(
            "easy_task_manager.handlers.start._send_task_lists",
            new_callable=AsyncMock,
        ) as send_lists_mock:
            await handle_lists_command(message=message, state=state)

        self.assertEqual(state.clear_count, 1)
        send_lists_mock.assert_awaited_once_with(message=message)

    async def test_family_command_opens_family_menu(self) -> None:
        message = SimpleNamespace(chat=SimpleNamespace(id=200), answer=AsyncMock())
        state = FakeState()

        await handle_family_command(message=message, state=state)

        self.assertEqual(state.clear_count, 1)
        message.answer.assert_awaited_once()
        self.assertEqual(message.answer.await_args.kwargs["text"], FAMILY_MENU_TEXT)

    async def test_help_command_sends_help_text(self) -> None:
        message = SimpleNamespace(chat=SimpleNamespace(id=200), answer=AsyncMock())
        state = FakeState()

        await handle_help_command(message=message, state=state)

        self.assertEqual(state.clear_count, 1)
        message.answer.assert_awaited_once_with(text=HELP_TEXT)

    async def test_create_family_callback_creates_family_and_shows_start(self) -> None:
        message = SimpleNamespace(chat=SimpleNamespace(id=300), answer=AsyncMock())
        callback = SimpleNamespace(
            message=message,
            from_user=SimpleNamespace(username="new_user", full_name="Новый пользователь"),
            answer=AsyncMock(),
        )
        state = FakeState()

        with patch(
            "easy_task_manager.handlers.start.family_storage.get_family_id_for_chat",
            return_value=None,
        ), patch(
            "easy_task_manager.handlers.start.family_storage.create_family_for_member",
        ) as create_mock:
            await handle_create_family_callback(callback=callback, state=state)

        create_mock.assert_called_once_with(chat_id=300, name="new_user")
        self.assertEqual(message.answer.await_args_list[0].kwargs["text"], FAMILY_CREATED_TEXT)
        self.assertEqual(message.answer.await_args_list[1].kwargs["text"], WELCOME_TEXT)

    async def test_join_family_callback_asks_for_invite_code(self) -> None:
        message = SimpleNamespace(chat=SimpleNamespace(id=300), answer=AsyncMock())
        callback = SimpleNamespace(message=message, answer=AsyncMock())
        state = FakeState()

        with patch(
            "easy_task_manager.handlers.start.family_storage.get_family_id_for_chat",
            return_value=None,
        ):
            await handle_join_family_callback(callback=callback, state=state)

        self.assertEqual(state.last_state, FamilyOnboardingStates.waiting_invite_code)
        message.answer.assert_awaited_once_with(text=JOIN_FAMILY_PROMPT_TEXT)

    async def test_join_family_code_adds_user_to_invite_family(self) -> None:
        message = SimpleNamespace(
            from_user=SimpleNamespace(username="masha", full_name="Маша"),
            chat=SimpleNamespace(id=301),
            text="ABC12345",
            answer=AsyncMock(),
            bot=SimpleNamespace(),
        )
        state = FakeState()
        member = SimpleNamespace(name="masha", family_id="family_a")

        with patch(
            "easy_task_manager.handlers.start.family_storage.join_family_by_invite",
            return_value=("success", member),
        ) as join_mock, patch(
            "easy_task_manager.handlers.start.send_family_action_notification",
            new_callable=AsyncMock,
        ) as notify_mock:
            await handle_join_family_code(message=message, state=state)

        join_mock.assert_called_once_with(chat_id=301, name="masha", code="ABC12345")
        notify_mock.assert_awaited_once_with(
            bot=message.bot,
            actor_chat_id=301,
            family_id="family_a",
            text="masha: присоединился к семейному списку",
        )
        self.assertEqual(state.clear_count, 1)
        self.assertEqual(message.answer.await_args_list[0].kwargs["text"], JOIN_FAMILY_SUCCESS_TEXT)
        self.assertEqual(message.answer.await_args_list[1].kwargs["text"], WELCOME_TEXT)

    async def test_join_family_code_cancel_returns_to_new_user_start(self) -> None:
        message = SimpleNamespace(
            from_user=SimpleNamespace(id=301, full_name="Маша"),
            chat=SimpleNamespace(id=301),
            text="отмена",
            answer=AsyncMock(),
        )
        state = FakeState()

        with patch(
            "easy_task_manager.handlers.start.family_storage.join_family_by_invite",
        ) as join_mock, patch(
            "easy_task_manager.handlers.start.family_storage.get_family_id_for_chat",
            return_value=None,
        ):
            await handle_join_family_code(message=message, state=state)

        join_mock.assert_not_called()
        self.assertEqual(state.clear_count, 1)
        message.answer.assert_awaited_once()
        self.assertEqual(message.answer.await_args.kwargs["text"], NEW_USER_TEXT)

    async def test_invite_callback_generates_code_for_current_family(self) -> None:
        invite = SimpleNamespace(code="ABC12345")
        message = SimpleNamespace(chat=SimpleNamespace(id=200), answer=AsyncMock())
        callback = SimpleNamespace(message=message, answer=AsyncMock())

        with patch(
            "easy_task_manager.handlers.start.family_storage.get_family_id_for_chat",
            return_value="default",
        ), patch(
            "easy_task_manager.handlers.start.family_storage.create_invite",
            return_value=invite,
        ) as invite_mock, patch(
            "easy_task_manager.handlers.start._get_bot_username",
            new_callable=AsyncMock,
            return_value=None,
        ):
            await handle_invite_callback(callback=callback)

        invite_mock.assert_called_once_with(created_by_chat_id=200)
        message.answer.assert_awaited_once_with(
            text=INVITE_TEXT_TEMPLATE.format(code="ABC12345")
        )

    async def test_family_menu_callback_shows_family_actions(self) -> None:
        message = SimpleNamespace(chat=SimpleNamespace(id=200), answer=AsyncMock())
        callback = SimpleNamespace(message=message, answer=AsyncMock())
        state = FakeState(data={"task_text": "Купить молоко"})

        await handle_family_menu_callback(callback=callback, state=state)

        callback.answer.assert_awaited_once()
        self.assertEqual(state.clear_count, 1)
        message.answer.assert_awaited_once()
        kwargs = message.answer.await_args.kwargs
        self.assertEqual(kwargs["text"], FAMILY_MENU_TEXT)
        keyboard = kwargs["reply_markup"].inline_keyboard
        self.assertEqual(keyboard[0][0].text, "Пригласить")
        self.assertEqual(keyboard[1][0].text, "Участники")
        self.assertEqual(keyboard[2][0].text, "Удалить семью")
        self.assertEqual(keyboard[3][0].text, "Назад")

    async def test_family_members_callback_shows_remove_buttons_for_owner(self) -> None:
        message = SimpleNamespace(chat=SimpleNamespace(id=200), answer=AsyncMock())
        callback = SimpleNamespace(message=message, answer=AsyncMock())
        state = FakeState()
        members = (
            SimpleNamespace(chat_id=200, name="Паша"),
            SimpleNamespace(chat_id=201, name="Маша"),
        )

        with patch(
            "easy_task_manager.handlers.start.family_storage.list_family_members",
            return_value=members,
        ) as members_mock, patch(
            "easy_task_manager.handlers.start.family_storage.get_family_owner_chat_id",
            return_value=200,
        ) as owner_mock:
            await handle_family_members_callback(callback=callback, state=state)

        callback.answer.assert_awaited_once()
        self.assertEqual(state.clear_count, 1)
        members_mock.assert_called_once_with(family_id="default")
        owner_mock.assert_called_once_with(family_id="default")
        kwargs = message.answer.await_args.kwargs
        self.assertEqual(kwargs["text"], f"{FAMILY_MEMBERS_TEXT}\nПаша\nМаша")
        keyboard = kwargs["reply_markup"].inline_keyboard
        self.assertEqual(keyboard[0][0].text, "Удалить Маша")
        self.assertEqual(keyboard[0][0].callback_data, "todo:family:member:remove:201")

    async def test_remove_family_member_callback_rejects_non_owner(self) -> None:
        message = SimpleNamespace(chat=SimpleNamespace(id=201), answer=AsyncMock())
        callback = SimpleNamespace(
            data="todo:family:member:remove:200",
            message=message,
            answer=AsyncMock(),
        )
        state = FakeState()

        with patch(
            "easy_task_manager.handlers.start.family_storage.get_family_owner_chat_id",
            return_value=200,
        ):
            await handle_remove_family_member_callback(callback=callback, state=state)

        callback.answer.assert_awaited_once()
        self.assertEqual(state.clear_count, 1)
        message.answer.assert_awaited_once_with(text=FAMILY_MEMBER_REMOVE_FORBIDDEN_TEXT)

    async def test_confirm_remove_family_member_removes_and_notifies_family(self) -> None:
        bot = SimpleNamespace(send_message=AsyncMock())
        message = SimpleNamespace(chat=SimpleNamespace(id=200), answer=AsyncMock(), bot=bot)
        callback = SimpleNamespace(
            data="todo:family:member:remove:confirm:201",
            message=message,
            answer=AsyncMock(),
        )
        state = FakeState()
        removed_member = SimpleNamespace(chat_id=201, family_id="default", name="masha")

        with patch(
            "easy_task_manager.handlers.start.family_storage.get_family_owner_chat_id",
            return_value=200,
        ), patch(
            "easy_task_manager.handlers.start.family_storage.list_family_chat_ids",
            return_value=(200, 201, 202),
        ), patch(
            "easy_task_manager.handlers.start.family_storage.remove_member",
            return_value=removed_member,
        ) as remove_mock, patch(
            "easy_task_manager.handlers.start._send_family_members",
            new_callable=AsyncMock,
        ) as send_members_mock:
            await handle_confirm_remove_family_member_callback(
                callback=callback,
                state=state,
            )

        callback.answer.assert_awaited_once()
        self.assertEqual(state.clear_count, 1)
        remove_mock.assert_called_once_with(family_id="default", chat_id=201)
        self.assertEqual(
            message.answer.await_args.kwargs["text"],
            FAMILY_MEMBER_REMOVED_TEXT_TEMPLATE.format(name="masha"),
        )
        self.assertEqual(
            bot.send_message.await_args_list[0].kwargs,
            {"chat_id": 201, "text": "masha: удален из семейного списка"},
        )
        self.assertEqual(
            bot.send_message.await_args_list[1].kwargs,
            {"chat_id": 202, "text": "masha: удален из семейного списка"},
        )
        send_members_mock.assert_awaited_once_with(message=message)

    async def test_delete_family_callback_asks_for_confirmation(self) -> None:
        message = SimpleNamespace(chat=SimpleNamespace(id=200), answer=AsyncMock())
        callback = SimpleNamespace(message=message, answer=AsyncMock())
        state = FakeState(data={"task_text": "Купить молоко"})

        await handle_delete_family_callback(callback=callback, state=state)

        callback.answer.assert_awaited_once()
        self.assertEqual(state.clear_count, 1)
        kwargs = message.answer.await_args.kwargs
        self.assertEqual(kwargs["text"], FAMILY_DELETE_CONFIRM_TEXT)
        keyboard = kwargs["reply_markup"].inline_keyboard
        self.assertEqual(keyboard[0][0].text, "Да, удалить")
        self.assertEqual(keyboard[0][1].text, "Отмена")

    async def test_cancel_delete_family_returns_to_family_menu_without_deleting(self) -> None:
        message = SimpleNamespace(chat=SimpleNamespace(id=200), answer=AsyncMock())
        callback = SimpleNamespace(message=message, answer=AsyncMock())
        state = FakeState(data={"task_text": "Купить молоко"})

        with patch("easy_task_manager.handlers.start.family_storage.delete_family") as delete_mock:
            await handle_cancel_delete_family_callback(callback=callback, state=state)

        callback.answer.assert_awaited_once()
        self.assertEqual(state.clear_count, 1)
        delete_mock.assert_not_called()
        self.assertEqual(message.answer.await_args_list[0].kwargs["text"], FAMILY_DELETE_CANCELLED_TEXT)
        self.assertEqual(message.answer.await_args_list[1].kwargs["text"], FAMILY_MENU_TEXT)

    async def test_confirm_delete_family_removes_family_tasks_and_notifies_other_member(self) -> None:
        bot = SimpleNamespace(send_message=AsyncMock())
        message = SimpleNamespace(chat=SimpleNamespace(id=200), answer=AsyncMock(), bot=bot)
        callback = SimpleNamespace(message=message, answer=AsyncMock())
        state = FakeState(data={"task_text": "Купить молоко"})

        with patch(
            "easy_task_manager.handlers.start.family_storage.get_family_id_for_chat",
            return_value="family_a",
        ), patch(
            "easy_task_manager.handlers.start.family_storage.delete_family",
            return_value=(200, 201),
        ) as delete_family_mock, patch(
            "easy_task_manager.handlers.start.task_storage.delete_tasks_by_family",
            return_value=2,
        ) as delete_tasks_mock, patch(
            "easy_task_manager.handlers.start.wake_reminder_scheduler",
        ) as wake_mock:
            await handle_confirm_delete_family_callback(callback=callback, state=state)

        callback.answer.assert_awaited_once()
        self.assertEqual(state.clear_count, 1)
        delete_family_mock.assert_called_once_with(family_id="family_a")
        delete_tasks_mock.assert_called_once_with(family_id="family_a")
        wake_mock.assert_called_once_with("family_deleted")
        bot.send_message.assert_awaited_once_with(chat_id=201, text=FAMILY_DELETED_TEXT)
        self.assertEqual(message.answer.await_args_list[0].kwargs["text"], FAMILY_DELETED_TEXT)
        self.assertEqual(message.answer.await_args_list[1].kwargs["text"], NEW_USER_TEXT)

    async def test_back_to_start_callback_shows_start(self) -> None:
        message = SimpleNamespace(
            from_user=SimpleNamespace(id=200),
            chat=SimpleNamespace(id=200),
            answer=AsyncMock(),
        )
        callback = SimpleNamespace(message=message, answer=AsyncMock())
        state = FakeState(data={"task_text": "Купить молоко"})

        await handle_back_to_start_callback(callback=callback, state=state)

        callback.answer.assert_awaited_once()
        self.assertEqual(state.clear_count, 1)
        self.assertEqual(message.answer.await_args.kwargs["text"], WELCOME_TEXT)

    async def test_task_lists_callback_shows_family_lists_with_counts(self) -> None:
        message = SimpleNamespace(chat=SimpleNamespace(id=200), answer=AsyncMock())
        callback = SimpleNamespace(message=message, answer=AsyncMock())
        task_lists = [
            SimpleNamespace(id="general", title="Общий"),
            SimpleNamespace(id="shopping", title="Покупки"),
        ]

        with patch(
            "easy_task_manager.handlers.start.task_list_storage.list_task_lists_by_family",
            return_value=task_lists,
        ) as lists_mock, patch(
            "easy_task_manager.handlers.start.task_storage.count_tasks_by_family_lists",
            return_value={"general": 3, "shopping": 1},
        ) as counts_mock:
            await handle_task_lists_callback(callback=callback)

        callback.answer.assert_awaited_once()
        lists_mock.assert_called_once_with(family_id="default")
        counts_mock.assert_called_once_with(family_id="default", now=ANY)
        message.answer.assert_awaited_once()
        kwargs = message.answer.await_args.kwargs
        self.assertEqual(kwargs["text"], f"{TASK_LISTS_TEXT}\nОбщий: 3\nПокупки: 1")
        keyboard = kwargs["reply_markup"].inline_keyboard
        self.assertEqual(keyboard[0][0].text, "Общий (3)")
        self.assertEqual(keyboard[0][0].callback_data, "todo:list:open:general")
        self.assertEqual(keyboard[1][0].text, "Покупки (1)")
        self.assertEqual(keyboard[1][0].callback_data, "todo:list:open:shopping")
        self.assertEqual(keyboard[2][0].text, "Добавить список")

    async def test_task_lists_add_callback_shows_missing_presets(self) -> None:
        message = SimpleNamespace(chat=SimpleNamespace(id=200), answer=AsyncMock())
        callback = SimpleNamespace(message=message, answer=AsyncMock())
        presets = [SimpleNamespace(id="shopping", title="Покупки")]

        with patch(
            "easy_task_manager.handlers.start.task_list_storage.list_missing_presets_by_family",
            return_value=presets,
        ) as presets_mock:
            await handle_task_lists_add_callback(callback=callback)

        presets_mock.assert_called_once_with(family_id="default")
        message.answer.assert_awaited_once()
        kwargs = message.answer.await_args.kwargs
        self.assertEqual(kwargs["text"], TASK_LISTS_ADD_TEXT)
        keyboard = kwargs["reply_markup"].inline_keyboard
        self.assertEqual(keyboard[0][0].text, "Покупки")
        self.assertEqual(keyboard[0][0].callback_data, "todo:lists:create:shopping")

    async def test_task_list_create_callback_creates_preset_and_returns_to_lists(self) -> None:
        message = SimpleNamespace(chat=SimpleNamespace(id=200), answer=AsyncMock())
        callback = SimpleNamespace(
            data="todo:lists:create:shopping",
            message=message,
            answer=AsyncMock(),
        )
        created = SimpleNamespace(id="shopping", title="Покупки")

        with patch(
            "easy_task_manager.handlers.start.task_list_storage.create_task_list_from_preset",
            return_value=created,
        ) as create_mock, patch(
            "easy_task_manager.handlers.start._send_task_lists",
            new_callable=AsyncMock,
        ) as send_lists_mock:
            await handle_task_list_create_callback(callback=callback)

        create_mock.assert_called_once_with(family_id="default", preset_id="shopping")
        self.assertEqual(
            message.answer.await_args.kwargs["text"],
            TASK_LIST_CREATED_TEMPLATE.format(title="Покупки"),
        )
        send_lists_mock.assert_awaited_once_with(message=message)

    async def test_task_list_open_callback_shows_selected_list(self) -> None:
        message = SimpleNamespace(chat=SimpleNamespace(id=200), answer=AsyncMock())
        callback = SimpleNamespace(
            data="todo:list:open:shopping",
            message=message,
            answer=AsyncMock(),
        )

        with patch(
            "easy_task_manager.handlers.start._send_task_list",
            new_callable=AsyncMock,
        ) as send_list_mock:
            await handle_task_list_open_callback(callback=callback)

        send_list_mock.assert_awaited_once_with(message=message, list_id="shopping")

    async def test_handle_list_callback_for_empty_tasks(self) -> None:
        message = SimpleNamespace(chat=SimpleNamespace(id=200), answer=AsyncMock())
        callback = SimpleNamespace(message=message, answer=AsyncMock())

        with patch(
            "easy_task_manager.handlers.start.task_list_storage.get_task_list",
            return_value=SimpleNamespace(id="general", title="Общий"),
        ), patch(
            "easy_task_manager.handlers.start.task_storage.list_tasks_by_family_and_list",
            return_value=[],
        ) as list_mock:
            await handle_list_callback(callback=callback)

        callback.answer.assert_awaited_once()
        list_mock.assert_called_once_with(family_id="default", list_id="general", now=ANY)
        message.answer.assert_awaited_once()
        kwargs = message.answer.await_args.kwargs
        self.assertEqual(kwargs["text"], LIST_EMPTY_TEXT)
        keyboard = kwargs["reply_markup"].inline_keyboard
        self.assertEqual(keyboard[0][0].text, "Добавить")
        self.assertEqual(keyboard[0][0].callback_data, "todo:add:list:general")

    async def test_handle_list_callback_sends_hints_for_existing_tasks(self) -> None:
        message = SimpleNamespace(chat=SimpleNamespace(id=200), answer=AsyncMock())
        callback = SimpleNamespace(message=message, answer=AsyncMock())
        tasks = [
            Task(
                id=3,
                chat_id=200,
                text="Купить молоко",
                deadline=date(2026, 6, 2),
                created_at=datetime.now(timezone.utc),
            ),
            Task(
                id=1,
                chat_id=200,
                text="Погулять",
                deadline=None,
                created_at=datetime.now(timezone.utc),
            ),
        ]

        with patch(
            "easy_task_manager.handlers.start.task_list_storage.get_task_list",
            return_value=SimpleNamespace(id="general", title="Общий"),
        ), patch(
            "easy_task_manager.handlers.start.task_storage.list_tasks_by_family_and_list",
            return_value=tasks,
        ):
            await handle_list_callback(callback=callback)

        self.assertEqual(message.answer.await_count, 2)
        first_kwargs = message.answer.await_args_list[0].kwargs
        second_kwargs = message.answer.await_args_list[1].kwargs
        self.assertEqual(
            first_kwargs["text"],
            "02.06.2026\n#3 Купить молоко\n\nБез дедлайна\n#1 Погулять",
        )
        self.assertEqual(second_kwargs["text"], LIST_HINTS_TEXT)
        self.assertEqual(second_kwargs["reply_markup"].inline_keyboard[0][0].text, "#3")
        self.assertEqual(second_kwargs["reply_markup"].inline_keyboard[0][1].text, "#1")
        self.assertEqual(second_kwargs["reply_markup"].inline_keyboard[1][0].text, "Добавить")
        self.assertEqual(
            second_kwargs["reply_markup"].inline_keyboard[1][0].callback_data,
            "todo:add:list:general",
        )

    async def test_handle_list_callback_paginates_existing_tasks(self) -> None:
        message = SimpleNamespace(chat=SimpleNamespace(id=200), answer=AsyncMock())
        callback = SimpleNamespace(message=message, answer=AsyncMock())
        tasks = [
            Task(
                id=task_id,
                chat_id=200,
                text=f"Дело {task_id}",
                deadline=None,
                created_at=datetime.now(timezone.utc),
            )
            for task_id in range(1, 8)
        ]

        with patch(
            "easy_task_manager.handlers.start.task_list_storage.get_task_list",
            return_value=SimpleNamespace(id="general", title="Общий"),
        ), patch(
            "easy_task_manager.handlers.start.task_storage.list_tasks_by_family_and_list",
            return_value=tasks,
        ):
            await handle_list_callback(callback=callback)

        self.assertEqual(message.answer.await_count, 2)
        self.assertNotIn("#7 Дело 7", message.answer.await_args_list[0].kwargs["text"])
        second_kwargs = message.answer.await_args_list[1].kwargs
        self.assertEqual(
            second_kwargs["text"],
            "Выбери задачу на этой странице.\nСтраница 1 из 2",
        )
        keyboard = second_kwargs["reply_markup"].inline_keyboard
        self.assertEqual([button.text for button in keyboard[0]], ["#1", "#2", "#3"])
        self.assertEqual([button.text for button in keyboard[1]], ["#4", "#5", "#6"])
        self.assertEqual([button.text for button in keyboard[2]], ["1/2", "→"])
        self.assertEqual(keyboard[2][1].callback_data, "todo:list:page:1:general")

    async def test_task_page_callback_opens_requested_page(self) -> None:
        message = SimpleNamespace(chat=SimpleNamespace(id=200), answer=AsyncMock())
        callback = SimpleNamespace(
            data="todo:list:page:1:general",
            message=message,
            answer=AsyncMock(),
        )
        tasks = [
            Task(
                id=task_id,
                chat_id=200,
                text=f"Дело {task_id}",
                deadline=None,
                created_at=datetime.now(timezone.utc),
            )
            for task_id in range(1, 8)
        ]

        with patch(
            "easy_task_manager.handlers.start.task_list_storage.get_task_list",
            return_value=SimpleNamespace(id="general", title="Общий"),
        ), patch(
            "easy_task_manager.handlers.start.task_storage.list_tasks_by_family_and_list",
            return_value=tasks,
        ):
            await handle_task_page_callback(callback=callback)

        callback.answer.assert_awaited_once()
        self.assertEqual(message.answer.await_args_list[0].kwargs["text"], "Без дедлайна\n#7 Дело 7")
        second_kwargs = message.answer.await_args_list[1].kwargs
        self.assertEqual(
            second_kwargs["text"],
            "Выбери задачу на этой странице.\nСтраница 2 из 2",
        )
        keyboard = second_kwargs["reply_markup"].inline_keyboard
        self.assertEqual(keyboard[0][0].callback_data, "todo:list:hint:7:1:general")
        self.assertEqual([button.text for button in keyboard[1]], ["←", "2/2"])
        self.assertEqual(keyboard[1][0].callback_data, "todo:list:page:0:general")

    async def test_task_hint_callback_sends_selected_task_with_actions(self) -> None:
        message = SimpleNamespace(chat=SimpleNamespace(id=200), answer=AsyncMock())
        callback = SimpleNamespace(
            data="todo:list:hint:1",
            message=message,
            answer=AsyncMock(),
        )
        task = Task(
            id=1,
            chat_id=200,
            text="Купить молоко",
            deadline=date(2026, 6, 1),
            created_at=datetime.now(timezone.utc),
        )

        with patch(
            "easy_task_manager.handlers.start.task_storage.get_task_by_family",
            return_value=task,
        ) as get_mock:
            await handle_task_hint_callback(callback=callback)

        callback.answer.assert_awaited_once()
        get_mock.assert_called_once_with(family_id="default", task_id=1)
        message.answer.assert_awaited_once()
        kwargs = message.answer.await_args.kwargs
        self.assertEqual(kwargs["text"], "01.06.2026\n#1 Купить молоко")
        keyboard = kwargs["reply_markup"].inline_keyboard
        self.assertEqual(keyboard[0][0].text, "Сделал")
        self.assertEqual(keyboard[0][0].callback_data, "todo:list:done:1")
        self.assertEqual(keyboard[0][1].text, "Отложить")
        self.assertEqual(keyboard[0][1].callback_data, "todo:list:snooze:menu:1:0:general")
        self.assertEqual(keyboard[1][0].text, "Дедлайн")
        self.assertEqual(keyboard[1][0].callback_data, "todo:list:deadline:menu:1")
        self.assertEqual(keyboard[1][1].text, "Изменить список")
        self.assertEqual(keyboard[1][1].callback_data, "todo:list:change-list:1:0:general")
        self.assertEqual(keyboard[2][0].text, "Повторять")
        self.assertEqual(keyboard[2][0].callback_data, "todo:list:recurrence:menu:1")
        self.assertEqual(keyboard[3][0].text, "Назад")
        self.assertEqual(keyboard[3][0].callback_data, "todo:list:back:general")

    async def test_task_hint_callback_preserves_page_in_task_actions(self) -> None:
        message = SimpleNamespace(chat=SimpleNamespace(id=200), answer=AsyncMock())
        callback = SimpleNamespace(
            data="todo:list:hint:7:1:general",
            message=message,
            answer=AsyncMock(),
        )
        task = Task(
            id=7,
            chat_id=200,
            text="Купить лейку",
            deadline=None,
            created_at=datetime.now(timezone.utc),
        )

        with patch(
            "easy_task_manager.handlers.start.task_storage.get_task_by_family",
            return_value=task,
        ):
            await handle_task_hint_callback(callback=callback)

        keyboard = message.answer.await_args.kwargs["reply_markup"].inline_keyboard
        self.assertEqual(keyboard[0][0].callback_data, "todo:list:done:7:1:general")
        self.assertEqual(
            keyboard[0][1].callback_data,
            "todo:list:snooze:menu:7:1:general",
        )
        self.assertEqual(
            keyboard[1][0].callback_data,
            "todo:list:deadline:menu:7:1:general",
        )
        self.assertEqual(keyboard[1][1].callback_data, "todo:list:change-list:7:1:general")
        self.assertEqual(keyboard[2][0].callback_data, "todo:list:recurrence:menu:7:1:general")
        self.assertEqual(keyboard[3][0].callback_data, "todo:list:back:1:general")

    async def test_task_deadline_menu_callback_sends_deadline_actions(self) -> None:
        message = SimpleNamespace(chat=SimpleNamespace(id=200), answer=AsyncMock())
        callback = SimpleNamespace(
            data="todo:list:deadline:menu:1",
            message=message,
            answer=AsyncMock(),
        )
        task = Task(
            id=1,
            chat_id=200,
            text="Купить молоко",
            deadline=date(2026, 6, 1),
            created_at=datetime.now(timezone.utc),
        )

        with patch(
            "easy_task_manager.handlers.start.task_storage.get_task_by_family",
            return_value=task,
        ) as get_mock:
            await handle_task_deadline_menu_callback(callback=callback)

        callback.answer.assert_awaited_once()
        get_mock.assert_called_once_with(family_id="default", task_id=1)
        message.answer.assert_awaited_once()
        kwargs = message.answer.await_args.kwargs
        self.assertEqual(kwargs["text"], "01.06.2026\n#1 Купить молоко")
        keyboard = kwargs["reply_markup"].inline_keyboard
        self.assertEqual(keyboard[0][0].text, "Сегодня")
        self.assertEqual(keyboard[0][0].callback_data, "todo:list:deadline:today:1")
        self.assertEqual(keyboard[0][1].text, "Завтра")
        self.assertEqual(keyboard[0][1].callback_data, "todo:list:deadline:tomorrow:1")
        self.assertEqual(keyboard[1][0].text, "Свой дедлайн")
        self.assertEqual(keyboard[1][0].callback_data, "todo:list:deadline:custom:1")
        self.assertEqual(keyboard[1][1].text, "Удалить дедлайн")
        self.assertEqual(keyboard[1][1].callback_data, "todo:list:deadline:remove:1")

    async def test_task_change_list_callback_shows_other_lists(self) -> None:
        message = SimpleNamespace(chat=SimpleNamespace(id=200), answer=AsyncMock())
        callback = SimpleNamespace(
            data="todo:list:change-list:1:0:general",
            message=message,
            answer=AsyncMock(),
        )
        task = Task(
            id=1,
            chat_id=200,
            text="Купить молоко",
            deadline=None,
            created_at=datetime.now(timezone.utc),
        )
        task_lists = [
            SimpleNamespace(id="general", title="Общий"),
            SimpleNamespace(id="shopping", title="Покупки"),
        ]

        with patch(
            "easy_task_manager.handlers.start.task_storage.get_task_by_family",
            return_value=task,
        ), patch(
            "easy_task_manager.handlers.start.task_list_storage.list_task_lists_by_family",
            return_value=task_lists,
        ):
            await handle_task_change_list_callback(callback=callback)

        callback.answer.assert_awaited_once()
        kwargs = message.answer.await_args.kwargs
        self.assertEqual(kwargs["text"], CHANGE_TASK_LIST_TEXT)
        keyboard = kwargs["reply_markup"].inline_keyboard
        self.assertEqual(keyboard[0][0].text, "Покупки")
        self.assertEqual(
            keyboard[0][0].callback_data,
            "todo:list:move-list:1:0:general:shopping",
        )

    async def test_task_move_to_list_callback_updates_task_and_opens_new_list(self) -> None:
        message = SimpleNamespace(chat=SimpleNamespace(id=200), answer=AsyncMock())
        callback = SimpleNamespace(
            data="todo:list:move-list:1:0:general:work",
            message=message,
            answer=AsyncMock(),
        )
        target_list = SimpleNamespace(id="work", title="Работа")
        updated_task = Task(
            id=1,
            chat_id=200,
            text="Подготовить отчет",
            deadline=None,
            list_id="work",
            created_at=datetime.now(timezone.utc),
        )

        with patch(
            "easy_task_manager.handlers.start.task_list_storage.get_task_list",
            return_value=target_list,
        ) as get_list_mock, patch(
            "easy_task_manager.handlers.start.task_storage.update_task_list_by_family",
            return_value=updated_task,
        ) as update_mock, patch(
            "easy_task_manager.handlers.start._send_task_list",
            new_callable=AsyncMock,
        ) as send_list_mock:
            await handle_task_move_to_list_callback(callback=callback)

        callback.answer.assert_awaited_once()
        get_list_mock.assert_called_once_with(family_id="default", list_id="work")
        update_mock.assert_called_once_with(
            family_id="default",
            task_id=1,
            list_id="work",
        )
        self.assertEqual(
            message.answer.await_args.kwargs["text"],
            TASK_LIST_CHANGED_TEMPLATE.format(title="Работа"),
        )
        send_list_mock.assert_awaited_once_with(message=message, list_id="work")

    async def test_task_deadline_today_callback_saves_date_and_asks_for_time(self) -> None:
        message = SimpleNamespace(chat=SimpleNamespace(id=200), answer=AsyncMock())
        callback = SimpleNamespace(
            data="todo:list:deadline:today:1",
            message=message,
            answer=AsyncMock(),
        )
        state = FakeState()
        task = Task(
            id=1,
            chat_id=200,
            text="Купить молоко",
            deadline=None,
            created_at=datetime.now(timezone.utc),
        )

        with patch(
            "easy_task_manager.handlers.start.task_storage.get_task_by_family",
            return_value=task,
        ) as get_mock, patch(
            "easy_task_manager.handlers.start.get_today_moscow",
            return_value=date(2026, 6, 2),
        ):
            await handle_task_deadline_today_callback(callback=callback, state=state)

        callback.answer.assert_awaited_once()
        get_mock.assert_called_once_with(
            family_id="default",
            task_id=1,
        )
        self.assertEqual(state.last_state, SelectedTaskDeadlineStates.waiting_deadline_time)
        self.assertEqual(state._data["selected_deadline_task_id"], 1)
        self.assertEqual(state._data["pending_deadline"], "2026-06-02")
        self.assertEqual(message.answer.await_count, 2)
        self.assertEqual(message.answer.await_args_list[0].kwargs["text"], DEADLINE_ADDED_TEXT)
        self.assertEqual(message.answer.await_args_list[1].kwargs["text"], ASK_DEADLINE_TIME_TEXT)

    async def test_task_deadline_custom_callback_asks_for_custom_date(self) -> None:
        message = SimpleNamespace(chat=SimpleNamespace(id=200), answer=AsyncMock())
        callback = SimpleNamespace(
            data="todo:list:deadline:custom:1",
            message=message,
            answer=AsyncMock(),
        )
        state = FakeState()
        task = Task(
            id=1,
            chat_id=200,
            text="Купить молоко",
            deadline=None,
            created_at=datetime.now(timezone.utc),
        )

        with patch(
            "easy_task_manager.handlers.start.task_storage.get_task_by_family",
            return_value=task,
        ) as get_mock:
            await handle_task_deadline_custom_callback(callback=callback, state=state)

        callback.answer.assert_awaited_once()
        get_mock.assert_called_once_with(family_id="default", task_id=1)
        self.assertEqual(state.last_state, SelectedTaskDeadlineStates.waiting_custom_deadline)
        self.assertEqual(state._data["selected_deadline_task_id"], 1)
        message.answer.assert_awaited_once_with(text=CUSTOM_DEADLINE_PROMPT_TEXT)

    async def test_selected_task_custom_deadline_saves_date_and_asks_for_time(self) -> None:
        message = SimpleNamespace(
            text="31.12.2099",
            chat=SimpleNamespace(id=200),
            answer=AsyncMock(),
        )
        state = FakeState(data={"selected_deadline_task_id": 1})
        task = Task(
            id=1,
            chat_id=200,
            text="Купить молоко",
            deadline=None,
            created_at=datetime.now(timezone.utc),
        )

        with patch(
            "easy_task_manager.handlers.start.task_storage.get_task_by_family",
            return_value=task,
        ) as get_mock:
            await handle_selected_task_custom_deadline(message=message, state=state)

        get_mock.assert_called_once_with(
            family_id="default",
            task_id=1,
        )
        self.assertEqual(state.last_state, SelectedTaskDeadlineStates.waiting_deadline_time)
        self.assertEqual(state._data["pending_deadline"], "2099-12-31")
        self.assertEqual(message.answer.await_count, 2)
        self.assertEqual(message.answer.await_args_list[0].kwargs["text"], DEADLINE_ADDED_TEXT)
        self.assertEqual(message.answer.await_args_list[1].kwargs["text"], ASK_DEADLINE_TIME_TEXT)

    async def test_selected_task_custom_deadline_invalid_asks_to_repeat(self) -> None:
        message = SimpleNamespace(
            text="завтра",
            chat=SimpleNamespace(id=200),
            answer=AsyncMock(),
        )
        state = FakeState(data={"selected_deadline_task_id": 1})

        await handle_selected_task_custom_deadline(message=message, state=state)

        message.answer.assert_awaited_once_with(text=CUSTOM_DEADLINE_INVALID_TEXT)
        self.assertEqual(state.clear_count, 0)

    async def test_selected_task_custom_deadline_cancel_returns_to_start_without_update(self) -> None:
        message = SimpleNamespace(
            text="Отмена",
            chat=SimpleNamespace(id=200),
            answer=AsyncMock(),
        )
        state = FakeState(data={"selected_deadline_task_id": 1})

        with patch(
            "easy_task_manager.handlers.start.task_storage.update_task_deadline_by_family",
        ) as update_mock:
            await handle_selected_task_custom_deadline(message=message, state=state)

        update_mock.assert_not_called()
        self.assertEqual(state.clear_count, 1)
        message.answer.assert_awaited_once()
        self.assertEqual(message.answer.await_args.kwargs["text"], WELCOME_TEXT)

    async def test_selected_task_deadline_time_skip_only_shows_updated_task(self) -> None:
        message = SimpleNamespace(chat=SimpleNamespace(id=200), answer=AsyncMock())
        callback = SimpleNamespace(
            data=DEADLINE_TIME_SKIP_CALLBACK,
            message=message,
            answer=AsyncMock(),
        )
        state = FakeState(
            data={"selected_deadline_task_id": 1, "pending_deadline": "2026-06-02"}
        )
        updated_task = Task(
            id=1,
            chat_id=200,
            text="Купить молоко",
            deadline=date(2026, 6, 2),
            created_at=datetime.now(timezone.utc),
        )

        with patch(
            "easy_task_manager.handlers.start.task_storage.update_task_deadline_by_family",
            return_value=updated_task,
        ) as update_mock, patch(
            "easy_task_manager.handlers.start._send_selected_task",
            new_callable=AsyncMock,
        ) as send_selected_mock, patch(
            "easy_task_manager.handlers.start.wake_reminder_scheduler"
        ) as wake_mock:
            await handle_selected_task_deadline_time_skip(callback=callback, state=state)

        callback.answer.assert_awaited_once()
        update_mock.assert_called_once_with(
            family_id="default",
            task_id=1,
            deadline=date(2026, 6, 2),
        )
        send_selected_mock.assert_awaited_once_with(
            message=message,
            task_id=1,
            list_id=None,
            page=0,
        )
        wake_mock.assert_called_once_with("task_deadline_updated")
        message.answer.assert_awaited_once_with(text=DEADLINE_ADDED_TEXT)
        self.assertEqual(state.clear_count, 1)

    async def test_selected_task_deadline_time_saves_time_and_shows_updated_task(self) -> None:
        message = SimpleNamespace(
            text="18:30",
            chat=SimpleNamespace(id=200),
            answer=AsyncMock(),
        )
        state = FakeState(
            data={"selected_deadline_task_id": 1, "pending_deadline": "2099-12-31"}
        )
        updated_task = Task(
            id=1,
            chat_id=200,
            text="Купить молоко",
            deadline=date(2099, 12, 31),
            deadline_time=time(18, 30),
            created_at=datetime.now(timezone.utc),
        )

        with patch(
            "easy_task_manager.handlers.start.task_storage.update_task_deadline_by_family",
            return_value=updated_task,
        ) as update_mock, patch(
            "easy_task_manager.handlers.start._send_selected_task",
            new_callable=AsyncMock,
        ) as send_selected_mock, patch(
            "easy_task_manager.handlers.start.wake_reminder_scheduler"
        ) as wake_mock:
            await handle_selected_task_deadline_time(message=message, state=state)

        update_mock.assert_called_once_with(
            family_id="default",
            task_id=1,
            deadline=date(2099, 12, 31),
            deadline_time=time(18, 30),
        )
        message.answer.assert_awaited_once_with(text=DEADLINE_TIME_ADDED_TEXT)
        send_selected_mock.assert_awaited_once_with(
            message=message,
            task_id=1,
            list_id=None,
            page=0,
        )
        wake_mock.assert_called_once_with("task_deadline_updated")
        self.assertEqual(state.clear_count, 1)

    async def test_selected_task_deadline_time_invalid_asks_to_repeat_without_update(self) -> None:
        message = SimpleNamespace(
            text="вечером",
            chat=SimpleNamespace(id=200),
            answer=AsyncMock(),
        )
        state = FakeState(
            data={"selected_deadline_task_id": 1, "pending_deadline": "2099-12-31"}
        )

        with patch(
            "easy_task_manager.handlers.start.task_storage.update_task_deadline_by_family",
        ) as update_mock:
            await handle_selected_task_deadline_time(message=message, state=state)

        message.answer.assert_awaited_once_with(text=CUSTOM_DEADLINE_TIME_INVALID_TEXT)
        update_mock.assert_not_called()
        self.assertEqual(state.clear_count, 0)

    async def test_selected_task_deadline_time_cancel_returns_to_start_without_update(self) -> None:
        message = SimpleNamespace(
            text="ОТМЕНА",
            chat=SimpleNamespace(id=200),
            answer=AsyncMock(),
        )
        state = FakeState(
            data={"selected_deadline_task_id": 1, "pending_deadline": "2099-12-31"}
        )

        with patch(
            "easy_task_manager.handlers.start.task_storage.update_task_deadline_by_family",
        ) as update_mock:
            await handle_selected_task_deadline_time(message=message, state=state)

        update_mock.assert_not_called()
        self.assertEqual(state.clear_count, 1)
        message.answer.assert_awaited_once()
        self.assertEqual(message.answer.await_args.kwargs["text"], WELCOME_TEXT)

    async def test_task_deadline_remove_callback_removes_deadline_and_shows_task(self) -> None:
        message = SimpleNamespace(chat=SimpleNamespace(id=200), answer=AsyncMock())
        callback = SimpleNamespace(
            data="todo:list:deadline:remove:1",
            message=message,
            answer=AsyncMock(),
        )
        state = FakeState()
        updated_task = Task(
            id=1,
            chat_id=200,
            text="Купить молоко",
            deadline=None,
            created_at=datetime.now(timezone.utc),
        )

        with patch(
            "easy_task_manager.handlers.start.task_storage.update_task_deadline_by_family",
            return_value=updated_task,
        ) as update_mock, patch(
            "easy_task_manager.handlers.start._send_selected_task",
            new_callable=AsyncMock,
        ) as send_selected_mock, patch(
            "easy_task_manager.handlers.start.wake_reminder_scheduler"
        ) as wake_mock:
            await handle_task_deadline_remove_callback(callback=callback, state=state)

        callback.answer.assert_awaited_once()
        update_mock.assert_called_once_with(family_id="default", task_id=1, deadline=None)
        message.answer.assert_awaited_once_with(text=DEADLINE_SKIPPED_TEXT)
        send_selected_mock.assert_awaited_once_with(
            message=message,
            task_id=1,
            list_id=None,
            page=0,
        )
        wake_mock.assert_called_once_with("task_deadline_removed")
        self.assertEqual(state.clear_count, 1)

    async def test_task_hint_callback_shows_current_list_when_task_missing(self) -> None:
        message = SimpleNamespace(chat=SimpleNamespace(id=200), answer=AsyncMock())
        callback = SimpleNamespace(
            data="todo:list:hint:99",
            message=message,
            answer=AsyncMock(),
        )
        tasks = [
            Task(
                id=3,
                chat_id=200,
                text="Погулять",
                deadline=None,
                created_at=datetime.now(timezone.utc),
            ),
        ]

        with patch(
            "easy_task_manager.handlers.start.task_storage.get_task_by_family",
            return_value=None,
        ), patch(
            "easy_task_manager.handlers.start.task_list_storage.get_task_list",
            return_value=SimpleNamespace(id="general", title="Общий"),
        ), patch(
            "easy_task_manager.handlers.start.task_storage.list_tasks_by_family_and_list",
            return_value=tasks,
        ):
            await handle_task_hint_callback(callback=callback)

        callback.answer.assert_awaited_once()
        self.assertEqual(message.answer.await_count, 2)
        self.assertEqual(message.answer.await_args_list[0].kwargs["text"], "Без дедлайна\n#3 Погулять")
        self.assertEqual(message.answer.await_args_list[1].kwargs["text"], LIST_HINTS_TEXT)

    async def test_task_done_callback_completes_task_and_returns_to_list(self) -> None:
        message = SimpleNamespace(chat=SimpleNamespace(id=200), answer=AsyncMock())
        callback = SimpleNamespace(
            data="todo:list:done:1",
            message=message,
            answer=AsyncMock(),
        )
        remaining_tasks = [
            Task(
                id=3,
                chat_id=200,
                text="Погулять",
                deadline=None,
                created_at=datetime.now(timezone.utc),
            ),
        ]
        completed_task = Task(
            id=1,
            chat_id=200,
            text="Купить молоко",
            deadline=None,
            created_at=datetime.now(timezone.utc),
            completed_at=datetime(2026, 6, 20, 9, 0, tzinfo=timezone.utc),
        )

        with patch(
            "easy_task_manager.handlers.start.task_storage.complete_task_once_by_family",
            return_value=(completed_task, True),
        ) as complete_mock, patch(
            "easy_task_manager.handlers.start.task_list_storage.get_task_list",
            return_value=SimpleNamespace(id="general", title="Общий"),
        ), patch(
            "easy_task_manager.handlers.start.task_storage.list_tasks_by_family_and_list",
            return_value=remaining_tasks,
        ), patch(
            "easy_task_manager.handlers.start.wake_reminder_scheduler"
        ) as wake_mock:
            await handle_task_done_callback(callback=callback)

        callback.answer.assert_awaited_once()
        complete_mock.assert_called_once_with(family_id="default", task_id=1)
        wake_mock.assert_called_once_with("task_done")
        self.assertEqual(message.answer.await_count, 3)
        self.assertEqual(message.answer.await_args_list[0].kwargs["text"], TASK_DONE_TEXT)
        self.assertEqual(message.answer.await_args_list[1].kwargs["text"], "Без дедлайна\n#3 Погулять")
        self.assertEqual(message.answer.await_args_list[2].kwargs["text"], LIST_HINTS_TEXT)

    async def test_task_done_callback_creates_next_recurring_task(self) -> None:
        message = SimpleNamespace(chat=SimpleNamespace(id=200), answer=AsyncMock())
        callback = SimpleNamespace(
            data="todo:list:done:1",
            message=message,
            answer=AsyncMock(),
        )
        completed_task = Task(
            id=1,
            chat_id=200,
            text="Оплатить интернет",
            deadline=date(2026, 6, 25),
            created_at=datetime.now(timezone.utc),
            recurrence="monthly",
            recurrence_anchor_day=25,
            completed_at=datetime(2026, 6, 25, 9, 0, tzinfo=timezone.utc),
        )
        next_task = Task(
            id=2,
            chat_id=200,
            text="Оплатить интернет",
            deadline=date(2026, 7, 25),
            created_at=datetime.now(timezone.utc),
            recurrence="monthly",
            recurrence_anchor_day=25,
        )

        with patch(
            "easy_task_manager.handlers.start.task_storage.complete_task_once_by_family",
            return_value=(completed_task, True),
        ), patch(
            "easy_task_manager.handlers.start.task_storage.add_task",
            return_value=next_task,
        ) as add_mock, patch(
            "easy_task_manager.handlers.start.task_list_storage.get_task_list",
            return_value=SimpleNamespace(id="general", title="Общий"),
        ), patch(
            "easy_task_manager.handlers.start.task_storage.list_tasks_by_family_and_list",
            return_value=[next_task],
        ), patch(
            "easy_task_manager.handlers.start.get_today_moscow",
            return_value=date(2026, 6, 25),
        ), patch(
            "easy_task_manager.handlers.start.wake_reminder_scheduler"
        ):
            await handle_task_done_callback(callback=callback)

        add_mock.assert_called_once_with(
            chat_id=200,
            text="Оплатить интернет",
            deadline=date(2026, 7, 25),
            deadline_time=None,
            family_id="default",
            list_id="general",
            recurrence="monthly",
            recurrence_anchor_day=25,
            note=None,
            reminder_enabled=True,
        )
        self.assertEqual(message.answer.await_args_list[0].kwargs["text"], TASK_DONE_TEXT)
        self.assertEqual(
            message.answer.await_args_list[1].kwargs["text"],
            "Следующий раз: 25.07.2026",
        )

    async def test_task_recurrence_monthly_callback_updates_task(self) -> None:
        message = SimpleNamespace(chat=SimpleNamespace(id=200), answer=AsyncMock())
        callback = SimpleNamespace(
            data="todo:list:recurrence:monthly:1",
            message=message,
            answer=AsyncMock(),
        )
        task = Task(
            id=1,
            chat_id=200,
            text="Оплатить интернет",
            deadline=date(2026, 6, 25),
            created_at=datetime.now(timezone.utc),
        )
        updated_task = Task(
            id=1,
            chat_id=200,
            text="Оплатить интернет",
            deadline=date(2026, 6, 25),
            created_at=datetime.now(timezone.utc),
            recurrence="monthly",
            recurrence_anchor_day=25,
        )

        with patch(
            "easy_task_manager.handlers.start.task_storage.get_task_by_family",
            side_effect=[task, updated_task],
        ), patch(
            "easy_task_manager.handlers.start.task_storage.update_task_recurrence_by_family",
            return_value=updated_task,
        ) as update_mock:
            await handle_task_recurrence_monthly_callback(callback=callback)

        update_mock.assert_called_once_with(
            family_id="default",
            task_id=1,
            recurrence="monthly",
        )
        self.assertEqual(
            message.answer.await_args_list[0].kwargs["text"],
            TASK_RECURRENCE_UPDATED_TEMPLATE.format(recurrence_label="каждый месяц"),
        )
        self.assertEqual(
            message.answer.await_args_list[1].kwargs["text"],
            "25.06.2026\n#1 Оплатить интернет (каждый месяц)",
        )

    async def test_task_recurrence_remove_callback_removes_recurrence(self) -> None:
        message = SimpleNamespace(chat=SimpleNamespace(id=200), answer=AsyncMock())
        callback = SimpleNamespace(
            data="todo:list:recurrence:remove:1",
            message=message,
            answer=AsyncMock(),
        )
        task = Task(
            id=1,
            chat_id=200,
            text="Оплатить интернет",
            deadline=date(2026, 6, 25),
            created_at=datetime.now(timezone.utc),
            recurrence="monthly",
            recurrence_anchor_day=25,
        )
        updated_task = Task(
            id=1,
            chat_id=200,
            text="Оплатить интернет",
            deadline=date(2026, 6, 25),
            created_at=datetime.now(timezone.utc),
        )

        with patch(
            "easy_task_manager.handlers.start.task_storage.get_task_by_family",
            side_effect=[task, updated_task],
        ), patch(
            "easy_task_manager.handlers.start.task_storage.update_task_recurrence_by_family",
            return_value=updated_task,
        ) as update_mock:
            await handle_task_recurrence_remove_callback(callback=callback)

        update_mock.assert_called_once_with(
            family_id="default",
            task_id=1,
            recurrence=None,
        )
        self.assertEqual(message.answer.await_args_list[0].kwargs["text"], TASK_RECURRENCE_REMOVED_TEXT)
        self.assertEqual(
            message.answer.await_args_list[1].kwargs["text"],
            "25.06.2026\n#1 Оплатить интернет",
        )

    async def test_task_back_callback_returns_to_list_without_delete(self) -> None:
        message = SimpleNamespace(chat=SimpleNamespace(id=200), answer=AsyncMock())
        callback = SimpleNamespace(
            data="todo:list:back",
            message=message,
            answer=AsyncMock(),
        )
        tasks = [
            Task(
                id=1,
                chat_id=200,
                text="Купить молоко",
                deadline=None,
                created_at=datetime.now(timezone.utc),
            ),
        ]

        with patch(
            "easy_task_manager.handlers.start.task_list_storage.get_task_list",
            return_value=SimpleNamespace(id="general", title="Общий"),
        ), patch(
            "easy_task_manager.handlers.start.task_storage.list_tasks_by_family_and_list",
            return_value=tasks,
        ) as list_mock, patch(
            "easy_task_manager.handlers.start.task_storage.delete_task_by_family"
        ) as delete_mock:
            await handle_task_back_callback(callback=callback)

        callback.answer.assert_awaited_once()
        list_mock.assert_called_once_with(family_id="default", list_id="general", now=ANY)
        delete_mock.assert_not_called()
        self.assertEqual(message.answer.await_count, 2)
        self.assertEqual(message.answer.await_args_list[0].kwargs["text"], "Без дедлайна\n#1 Купить молоко")
        self.assertEqual(message.answer.await_args_list[1].kwargs["text"], LIST_HINTS_TEXT)


if __name__ == "__main__":
    unittest.main()
