import unittest
from unittest.mock import AsyncMock

from aiogram.types import MenuButtonCommands, MenuButtonWebApp

from easy_task_manager.main import configure_bot_menu


class MainTests(unittest.IsolatedAsyncioTestCase):
    async def test_configure_bot_menu_sets_telegram_commands(self) -> None:
        bot = AsyncMock()

        await configure_bot_menu(bot)

        bot.set_my_commands.assert_awaited_once()
        commands = bot.set_my_commands.await_args.args[0]
        self.assertEqual(
            [command.command for command in commands],
            ["menu", "add", "lists", "family", "help"],
        )
        self.assertEqual(commands[0].description, "Открыть меню")
        button = bot.set_chat_menu_button.await_args.kwargs["menu_button"]
        self.assertIsInstance(button, MenuButtonCommands)

    async def test_configure_bot_menu_sets_persistent_web_app_button(self) -> None:
        bot = AsyncMock()

        await configure_bot_menu(bot, webapp_url="https://kotik.pavelmarchik.ru")

        bot.set_chat_menu_button.assert_awaited_once()
        button = bot.set_chat_menu_button.await_args.kwargs["menu_button"]
        self.assertIsInstance(button, MenuButtonWebApp)
        self.assertEqual(button.text, "Котик")
        self.assertEqual(button.web_app.url, "https://kotik.pavelmarchik.ru")


if __name__ == "__main__":
    unittest.main()
