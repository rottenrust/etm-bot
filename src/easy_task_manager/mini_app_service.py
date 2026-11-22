"""Shared domain service for Telegram Mini App and bot-facing flows."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Optional

from easy_task_manager.action_notifications import (
    MessageSender,
    build_task_deleted_notification,
    build_family_member_removed_notification,
    build_task_created_notification,
    build_task_done_notification,
    send_family_action_notification,
)
from easy_task_manager.deadline_utils import get_now_moscow, get_today_moscow, get_tomorrow_moscow
from easy_task_manager.family_storage import FamilyMember, JsonFamilyStorage
from easy_task_manager.recurrence import calculate_next_deadline
from easy_task_manager.task_list_storage import (
    DEFAULT_TASK_LIST_ID,
    TASK_LIST_PRESETS,
    JsonTaskListStorage,
    TaskList,
)
from easy_task_manager.task_storage import JsonTaskStorage, Task
from easy_task_manager.reminder_wakeup import wake_reminder_scheduler


@dataclass(frozen=True)
class MiniAppUser:
    """Current Telegram user resolved from WebApp init data."""

    chat_id: int
    name: str
    username: Optional[str] = None


class MiniAppAccessError(RuntimeError):
    """Raised when a Mini App user is not attached to a family."""


class MiniAppNotFoundError(RuntimeError):
    """Raised when requested Mini App resource does not exist."""


class MiniAppForbiddenError(RuntimeError):
    """Raised when a Mini App action is not allowed for the current user."""


class MiniAppService:
    """Coordinates family, task-list and task storage for Mini App API."""

    def __init__(
        self,
        task_storage: JsonTaskStorage,
        task_list_storage: JsonTaskListStorage,
        family_storage: JsonFamilyStorage,
        bot: MessageSender | None = None,
    ) -> None:
        self.task_storage = task_storage
        self.task_list_storage = task_list_storage
        self.family_storage = family_storage
        self.bot = bot

    def get_me(self, user: MiniAppUser) -> dict[str, object]:
        family_id = self._get_family_id_or_none(user.chat_id)
        member = self.family_storage.get_member(chat_id=user.chat_id)
        return {
            "user": {
                "chatId": user.chat_id,
                "name": member.name if member else user.name,
                "username": user.username,
            },
            "familyId": family_id,
            "hasFamily": family_id is not None,
        }

    def create_family(self, user: MiniAppUser) -> dict[str, object]:
        member = self.family_storage.create_family_for_member(
            chat_id=user.chat_id,
            name=user.name,
        )
        self.task_list_storage.ensure_default_task_list(family_id=member.family_id)
        return self.get_me(user)

    def get_home(
        self,
        user: MiniAppUser,
        mode: str = "nearest",
        selected_date: Optional[date] = None,
    ) -> dict[str, object]:
        family_id = self._get_family_id(user.chat_id)
        now = get_now_moscow()
        today = get_today_moscow()
        tomorrow = get_tomorrow_moscow()
        task_lists = self.task_list_storage.list_task_lists_by_family(family_id=family_id)
        list_titles = {task_list.id: task_list.title for task_list in task_lists}
        tasks = self.task_storage.list_tasks_by_family(
            family_id=family_id,
            now=now,
            include_completed=True,
        )
        if mode == "calendar" and selected_date is not None:
            section_dates = (selected_date, date.fromordinal(selected_date.toordinal() + 1))
        else:
            section_dates = (today, tomorrow)

        active_tasks = [task for task in tasks if task.completed_at is None]
        overdue = [task for task in tasks if task.deadline is not None and task.deadline < today]
        active_overdue = [task for task in active_tasks if task.deadline is not None and task.deadline < today]
        today_count = len([task for task in active_tasks if task.deadline == today])
        sections: list[dict[str, object]] = []
        sections.append(
            {
                "id": "overdue",
                "title": "Просрочено",
                "date": None,
                "tone": "purple",
                "tasks": [serialize_task(task, list_titles) for task in overdue],
            }
        )

        for index, current_date in enumerate(section_dates):
            if mode == "calendar":
                title = "Сегодня" if index == 0 else "Завтра"
            else:
                title = _date_section_title(current_date, today, tomorrow)
            sections.append(
                {
                    "id": current_date.isoformat(),
                    "title": title,
                    "date": current_date.isoformat(),
                    "tone": "green",
                    "tasks": [
                        serialize_task(task, list_titles)
                        for task in tasks
                        if task.deadline == current_date
                    ],
                }
            )

        if mode != "calendar":
            without_deadline = [task for task in tasks if task.deadline is None]
            if without_deadline:
                sections.append(
                    {
                        "id": "no-deadline",
                        "title": "Без дедлайна",
                        "date": None,
                        "tone": "green",
                        "tasks": [
                            serialize_task(task, list_titles) for task in without_deadline
                        ],
                    }
                )

        return {
            "mode": mode,
            "today": today.isoformat(),
            "selectedDate": (selected_date or today).isoformat(),
            "stats": {
                "today": today_count,
                "overdue": len(active_overdue),
            },
            "calendar": build_calendar_days(
                today,
                selected_date or today,
                {task.deadline for task in tasks if task.deadline is not None},
            ),
            "sections": sections,
        }

    def list_categories(self, user: MiniAppUser) -> dict[str, object]:
        family_id = self._get_family_id(user.chat_id)
        task_lists = self.task_list_storage.list_task_lists_by_family(family_id=family_id)
        counts = self.task_storage.count_tasks_by_family_lists(
            family_id=family_id,
            now=get_now_moscow(),
        )
        list_titles = {task_list.id: task_list.title for task_list in task_lists}
        tasks_by_list = {
            task_list.id: [
                serialize_task(task, list_titles)
                for task in self.task_storage.list_tasks_by_family_and_list(
                    family_id=family_id,
                    list_id=task_list.id,
                    now=get_now_moscow(),
                    include_completed=True,
                )
            ]
            for task_list in task_lists
        }
        return {
            "categories": [
                serialize_task_list(task_list, counts, tasks_by_list.get(task_list.id, []))
                for task_list in task_lists
            ],
            "missingPresets": [
                {"id": preset.id, "title": preset.title}
                for preset in self.task_list_storage.list_missing_presets_by_family(
                    family_id=family_id,
                )
            ],
            "presets": [{"id": preset.id, "title": preset.title} for preset in TASK_LIST_PRESETS],
        }

    async def create_task(
        self,
        user: MiniAppUser,
        text: str,
        deadline: Optional[date],
        deadline_time: Optional[time],
        list_id: str,
        note: Optional[str],
        reminder_enabled: bool,
    ) -> dict[str, object]:
        family_id = self._get_family_id(user.chat_id)
        task_list = self._get_task_list_or_default(family_id, list_id)
        task = self.task_storage.add_task(
            chat_id=user.chat_id,
            text=text,
            deadline=deadline,
            deadline_time=deadline_time,
            family_id=family_id,
            list_id=task_list.id,
            note=note,
            reminder_enabled=reminder_enabled,
        )
        await self._notify(
            user.chat_id,
            family_id,
            build_task_created_notification(self._member_name(user), task),
        )
        wake_reminder_scheduler("mini_app_task_created")
        return {"task": serialize_task(task, {task_list.id: task_list.title})}

    async def update_task(
        self,
        user: MiniAppUser,
        task_id: int,
        text: str,
        deadline: Optional[date],
        deadline_time: Optional[time],
        list_id: str,
        note: Optional[str],
        reminder_enabled: bool,
    ) -> dict[str, object]:
        family_id = self._get_family_id(user.chat_id)
        task_list = self._get_task_list_or_default(family_id, list_id)
        task = self.task_storage.update_task_by_family(
            family_id=family_id,
            task_id=task_id,
            text=text,
            deadline=deadline,
            deadline_time=deadline_time,
            list_id=task_list.id,
            note=note,
            reminder_enabled=reminder_enabled,
        )
        if task is None:
            raise MiniAppNotFoundError("Task not found.")
        await self._notify(
            user.chat_id,
            family_id,
            f"{self._member_name(user)}: задача изменена\n#{task.id} {task.text}",
        )
        wake_reminder_scheduler("mini_app_task_updated")
        return {"task": serialize_task(task, {task_list.id: task_list.title})}

    async def complete_task(self, user: MiniAppUser, task_id: int) -> dict[str, object]:
        family_id = self._get_family_id(user.chat_id)
        task, changed = self.task_storage.complete_task_once_by_family(
            family_id=family_id,
            task_id=task_id,
        )
        if task is None:
            raise MiniAppNotFoundError("Task not found.")
        if changed:
            self._create_next_recurring_task(task)
            await self._notify(
                user.chat_id,
                family_id,
                build_task_done_notification(self._member_name(user), task),
            )
            wake_reminder_scheduler("mini_app_task_completed")
        return {"task": serialize_task(task, {})}

    async def delete_task(self, user: MiniAppUser, task_id: int) -> dict[str, object]:
        family_id = self._get_family_id(user.chat_id)
        task = self.task_storage.delete_task_by_family(family_id, task_id)
        if task is None:
            raise MiniAppNotFoundError("Task not found.")
        await self._notify(
            user.chat_id,
            family_id,
            build_task_deleted_notification(self._member_name(user), task),
        )
        wake_reminder_scheduler("mini_app_task_deleted")
        return {"deleted": True, "taskId": task.id}

    def enable_preset(self, user: MiniAppUser, preset_id: str) -> dict[str, object]:
        family_id = self._get_family_id(user.chat_id)
        task_list = self.task_list_storage.create_task_list_from_preset(
            family_id=family_id,
            preset_id=preset_id,
        )
        if task_list is None:
            raise MiniAppNotFoundError("Category preset not found.")
        return {"category": serialize_task_list(task_list, {}, [])}

    def get_family(self, user: MiniAppUser) -> dict[str, object]:
        family_id = self._get_family_id(user.chat_id)
        owner_chat_id = self.family_storage.get_family_owner_chat_id(family_id=family_id)
        members = self.family_storage.list_family_members(family_id=family_id)
        return {
            "familyId": family_id,
            "ownerChatId": owner_chat_id,
            "canManageMembers": owner_chat_id == user.chat_id,
            "members": [serialize_member(member) for member in members],
        }

    async def create_invite(self, user: MiniAppUser) -> dict[str, object]:
        self._get_family_id(user.chat_id)
        invite = self.family_storage.create_invite(created_by_chat_id=user.chat_id)
        if invite is None:
            raise MiniAppAccessError("Family not found.")
        bot_link = None
        if self.bot is not None and hasattr(self.bot, "get_me"):
            try:
                bot_user = await self.bot.get_me()
                username = getattr(bot_user, "username", None)
                if username:
                    bot_link = f"https://t.me/{username}?start={invite.code}"
            except Exception:
                bot_link = None
        return {"code": invite.code, "botLink": bot_link}

    async def remove_family_member(self, user: MiniAppUser, chat_id: int) -> dict[str, object]:
        family_id = self._get_family_id(user.chat_id)
        owner_chat_id = self.family_storage.get_family_owner_chat_id(family_id=family_id)
        if owner_chat_id != user.chat_id:
            raise MiniAppForbiddenError("Only family owner can remove members.")
        if chat_id == user.chat_id:
            raise MiniAppForbiddenError("Owner cannot remove self.")
        members_before = self.family_storage.list_family_chat_ids(family_id=family_id)
        removed = self.family_storage.remove_member(family_id=family_id, chat_id=chat_id)
        if removed is None:
            raise MiniAppNotFoundError("Member not found.")
        if self.bot is not None:
            await send_family_action_notification(
                bot=self.bot,
                actor_chat_id=user.chat_id,
                family_id=family_id,
                text=build_family_member_removed_notification(removed.name),
                storage=self.family_storage,
                recipient_chat_ids=tuple(
                    member_chat_id
                    for member_chat_id in members_before
                    if member_chat_id != user.chat_id
                ),
            )
        return self.get_family(user)

    def _get_family_id_or_none(self, chat_id: int) -> Optional[str]:
        return self.family_storage.get_family_id_for_chat(chat_id=chat_id)

    def _get_family_id(self, chat_id: int) -> str:
        family_id = self._get_family_id_or_none(chat_id)
        if family_id is None:
            raise MiniAppAccessError("User is not attached to a family.")
        return family_id

    def _get_task_list_or_default(self, family_id: str, list_id: str) -> TaskList:
        if list_id == DEFAULT_TASK_LIST_ID:
            return self.task_list_storage.ensure_default_task_list(family_id=family_id)
        task_list = self.task_list_storage.get_task_list(
            family_id=family_id,
            list_id=list_id,
        )
        if task_list is None:
            raise MiniAppNotFoundError("Category not found.")
        return task_list

    def _create_next_recurring_task(self, task: Task) -> Optional[Task]:
        if task.deadline is None or task.recurrence is None:
            return None
        next_deadline = calculate_next_deadline(
            deadline=task.deadline,
            recurrence=task.recurrence,
            today=get_today_moscow(),
            anchor_day=task.recurrence_anchor_day,
        )
        if next_deadline is None:
            return None
        return self.task_storage.add_task(
            chat_id=task.chat_id,
            text=task.text,
            deadline=next_deadline,
            deadline_time=task.deadline_time,
            family_id=task.family_id,
            list_id=task.list_id,
            recurrence=task.recurrence,
            recurrence_anchor_day=task.recurrence_anchor_day,
            note=task.note,
            reminder_enabled=task.reminder_enabled,
        )

    async def _notify(self, actor_chat_id: int, family_id: str, text: str) -> None:
        if self.bot is None:
            return
        await send_family_action_notification(
            bot=self.bot,
            actor_chat_id=actor_chat_id,
            family_id=family_id,
            text=text,
            storage=self.family_storage,
        )

    def _member_name(self, user: MiniAppUser) -> str:
        member = self.family_storage.get_member(chat_id=user.chat_id)
        return member.name if member is not None else user.name


def serialize_task(task: Task, list_titles: dict[str, str]) -> dict[str, object]:
    return {
        "id": task.id,
        "text": task.text,
        "deadline": task.deadline.isoformat() if task.deadline else None,
        "deadlineTime": task.deadline_time.strftime("%H:%M") if task.deadline_time else None,
        "createdAt": task.created_at.isoformat(),
        "familyId": task.family_id,
        "listId": task.list_id,
        "listTitle": list_titles.get(task.list_id),
        "note": task.note,
        "reminderEnabled": task.reminder_enabled,
        "completedAt": task.completed_at.isoformat() if task.completed_at else None,
        "recurrence": task.recurrence,
        "recurrenceAnchorDay": task.recurrence_anchor_day,
        "snoozedUntil": task.snoozed_until.isoformat() if task.snoozed_until else None,
    }


def serialize_task_list(
    task_list: TaskList,
    counts: dict[str, int],
    tasks: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "id": task_list.id,
        "title": task_list.title,
        "count": counts.get(task_list.id, 0),
        "tasks": tasks,
    }


def serialize_member(member: FamilyMember) -> dict[str, object]:
    return {
        "chatId": member.chat_id,
        "familyId": member.family_id,
        "name": member.name,
        "joinedAt": member.joined_at.isoformat(),
    }


def build_calendar_days(
    start: date,
    selected_date: date,
    task_dates: set[date] | None = None,
) -> list[dict[str, object]]:
    task_dates = task_dates or set()
    start_ordinal = start.toordinal()
    selected_ordinal = selected_date.toordinal()
    if selected_ordinal >= start_ordinal + 24:
        start_ordinal = max(start_ordinal, selected_ordinal - 15)
    elif selected_ordinal < start_ordinal:
        start_ordinal = max(1, selected_ordinal - 15)
    final_ordinal = min(date.max.toordinal(), start_ordinal + 30)
    return [
        {
            "date": current.isoformat(),
            "weekday": _weekday_label(current),
            "day": current.day,
            "selected": current == selected_date,
            "hasTasks": current in task_dates,
        }
        for ordinal in range(start_ordinal, final_ordinal + 1)
        if (current := date.fromordinal(ordinal))
    ]


def _date_section_title(value: date, today: date, tomorrow: date) -> str:
    if value == today:
        return "Сегодня"
    if value == tomorrow:
        return "Завтра"
    return value.strftime("%d.%m.%Y")


def _weekday_label(value: date) -> str:
    return ("Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс")[value.weekday()]
