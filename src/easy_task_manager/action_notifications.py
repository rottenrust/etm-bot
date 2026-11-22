"""Family action notifications."""

from __future__ import annotations

import logging
from typing import Protocol

from easy_task_manager.config import get_families_file_path
from easy_task_manager.deadline_utils import (
    format_deadline_for_user,
    format_snooze_until_for_user,
)
from easy_task_manager.family_storage import JsonFamilyStorage
from easy_task_manager.list_tasks_contract import build_task_list_text
from easy_task_manager.start_contract import (
    FAMILY_MEMBER_JOINED_TEXT_TEMPLATE,
    FAMILY_MEMBER_REMOVED_TEXT_TEMPLATE,
)
from easy_task_manager.task_storage import Task

logger = logging.getLogger(__name__)
family_storage = JsonFamilyStorage(file_path=get_families_file_path())


class MessageSender(Protocol):
    async def send_message(self, chat_id: int, text: str) -> None:
        """Send message to Telegram chat."""


def build_task_created_notification(author_name: str, task: Task) -> str:
    return f"{author_name}: задача добавлена\n{build_task_list_text([task])}"


def build_task_done_notification(author_name: str, task: Task) -> str:
    return f"{author_name}: задача завершена\n{build_task_list_text([task])}"


def build_task_deadline_updated_notification(author_name: str, task: Task) -> str:
    if task.deadline is None:
        return f"{author_name}: дедлайн удален\n#{task.id} {task.text}"
    return (
        f"{author_name}: дедлайн изменен\n"
        f"#{task.id} {task.text} -> "
        f"{format_deadline_for_user(task.deadline, task.deadline_time)}"
    )


def build_task_snoozed_notification(author_name: str, task: Task) -> str:
    if task.snoozed_until is None:
        return f"{author_name}: отложение убрано\n#{task.id} {task.text}"
    return (
        f"{author_name}: задача отложена до "
        f"{format_snooze_until_for_user(task.snoozed_until)}\n"
        f"#{task.id} {task.text}"
    )


def build_family_member_joined_notification(member_name: str) -> str:
    return FAMILY_MEMBER_JOINED_TEXT_TEMPLATE.format(name=member_name)


def build_family_member_removed_notification(member_name: str) -> str:
    return FAMILY_MEMBER_REMOVED_TEXT_TEMPLATE.format(name=member_name)


async def send_family_action_notification(
    bot: MessageSender,
    actor_chat_id: int,
    text: str,
    family_id: str | None = None,
    storage: JsonFamilyStorage | None = None,
    recipient_chat_ids: tuple[int, ...] | None = None,
) -> int:
    """Send action notification to every family member except the actor."""
    target_storage = storage or family_storage
    sent_count = 0
    if family_id is None:
        member = target_storage.get_member(chat_id=actor_chat_id)
        if member is None:
            return 0
        family_id = member.family_id

    if recipient_chat_ids is None:
        recipient_chat_ids = target_storage.list_other_family_chat_ids(
            family_id=family_id,
            actor_chat_id=actor_chat_id,
        )
    for chat_id in recipient_chat_ids:
        try:
            await bot.send_message(chat_id=chat_id, text=text)
        except Exception:
            logger.exception(
                "family_action_notification_failed actor_chat_id=%s recipient_chat_id=%s",
                actor_chat_id,
                chat_id,
            )
            continue
        sent_count += 1
    return sent_count


def build_task_deleted_notification(actor_name: str, task: Task) -> str:
    return f"{actor_name}: задача удалена\n#{task.id} {task.text}"
