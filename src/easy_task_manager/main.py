"""Application entrypoint for polling mode."""

from __future__ import annotations

import asyncio
import logging
from contextlib import suppress

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand, MenuButtonCommands, MenuButtonWebApp, WebAppInfo
from aiohttp import web

from easy_task_manager.config import (
    ConfigError,
    get_bot_token,
    get_configured_family_members,
    get_families_file_path,
    get_reminder_state_file_path,
    get_task_lists_file_path,
    get_tasks_file_path,
    get_webapp_url,
)
from easy_task_manager.family_storage import JsonFamilyStorage
from easy_task_manager.handlers.add_task import router as add_task_router
from easy_task_manager.handlers.start import router as start_router
from easy_task_manager.reminder_wakeup import configure_reminder_wakeup
from easy_task_manager.reminders import run_due_task_reminder_scheduler
from easy_task_manager.reminder_state_storage import JsonReminderStateStorage
from easy_task_manager.start_contract import BOT_MENU_COMMANDS
from easy_task_manager.task_list_storage import JsonTaskListStorage
from easy_task_manager.task_storage import JsonTaskStorage


async def configure_bot_menu(bot: Bot, webapp_url: str | None = None) -> None:
    await bot.set_my_commands(
        [
            BotCommand(command=command.command, description=command.description)
            for command in BOT_MENU_COMMANDS
        ]
    )
    menu_button = (
        MenuButtonWebApp(text="Котик", web_app=WebAppInfo(url=webapp_url))
        if webapp_url
        else MenuButtonCommands()
    )
    await bot.set_chat_menu_button(menu_button=menu_button)


async def run() -> None:
    token = get_bot_token()
    webapp_url = get_webapp_url()
    bot = Bot(token=token)
    await configure_bot_menu(bot, webapp_url=webapp_url)
    dispatcher = Dispatcher()
    dispatcher.include_router(add_task_router)
    dispatcher.include_router(start_router)
    family_storage = JsonFamilyStorage(file_path=get_families_file_path())
    family_storage.initialize(default_members=get_configured_family_members())
    task_storage = JsonTaskStorage(file_path=get_tasks_file_path())
    task_storage.initialize()
    task_list_storage = JsonTaskListStorage(file_path=get_task_lists_file_path())
    task_list_storage.initialize()
    reminder_state = JsonReminderStateStorage(file_path=get_reminder_state_file_path())
    reminder_state.initialize()
    reminder_wakeup_event = asyncio.Event()
    configure_reminder_wakeup(reminder_wakeup_event)
    reminder_task = asyncio.create_task(
        run_due_task_reminder_scheduler(
            bot=bot,
            storage=task_storage,
            reminder_state=reminder_state,
            wakeup_event=reminder_wakeup_event,
        )
    )
    web_runner: web.AppRunner | None = None
    try:
        if webapp_url:
            from easy_task_manager.server import create_app

            app = create_app(
                task_storage=task_storage,
                task_list_storage=task_list_storage,
                family_storage=family_storage,
                bot=bot,
                bot_token=token,
            )
            web_runner = web.AppRunner(app, access_log=None)
            await web_runner.setup()
            site = web.TCPSite(web_runner, "127.0.0.1", 8003)
            await site.start()
            logging.getLogger(__name__).info("mini_app_listening address=127.0.0.1 port=8003")
        await dispatcher.start_polling(bot, allowed_updates=dispatcher.resolve_used_update_types())
    finally:
        if web_runner is not None:
            await web_runner.cleanup()
        reminder_task.cancel()
        with suppress(asyncio.CancelledError):
            await reminder_task
        await bot.session.close()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    try:
        asyncio.run(run())
    except ConfigError as error:
        logging.getLogger(__name__).error(str(error))
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
