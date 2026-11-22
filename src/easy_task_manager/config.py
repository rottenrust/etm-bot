"""Runtime configuration for the bot."""

import os
from pathlib import Path
from typing import Optional
from urllib.parse import urlsplit


class ConfigError(RuntimeError):
    """Raised when required runtime configuration is missing."""


def get_webapp_url() -> Optional[str]:
    """Return the public HTTPS Mini App URL when it is configured."""
    value = os.getenv("WEBAPP_URL", "").strip().rstrip("/")
    if not value:
        return None
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
        raise ConfigError("WEBAPP_URL must be an HTTPS URL.")
    return value


def get_bot_token() -> str:
    """Load BOT_TOKEN from environment and validate it."""
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise ConfigError("Environment variable BOT_TOKEN is required.")
    return token


def get_tasks_file_path() -> Path:
    """Load path to tasks JSON file from env or use default project path."""
    raw_path = os.getenv("TASKS_FILE", "").strip()
    if raw_path:
        return Path(raw_path)
    return Path(__file__).resolve().parents[2] / "data" / "tasks.json"


def get_task_lists_file_path() -> Path:
    """Load path to task lists JSON file from env or use default project path."""
    raw_path = os.getenv("TASK_LISTS_FILE", "").strip()
    if raw_path:
        return Path(raw_path)
    return Path(__file__).resolve().parents[2] / "data" / "task_lists.json"


def get_reminder_state_file_path() -> Path:
    """Load path to reminder state JSON file from env or use default project path."""
    raw_path = os.getenv("REMINDER_STATE_FILE", "").strip()
    if raw_path:
        return Path(raw_path)
    return Path(__file__).resolve().parents[2] / "data" / "reminder_state.json"


def get_families_file_path() -> Path:
    """Load path to families JSON file from env or use default project path."""
    raw_path = os.getenv("FAMILIES_FILE", "").strip()
    if raw_path:
        return Path(raw_path)
    return Path(__file__).resolve().parents[2] / "data" / "families.json"


def get_configured_family_members() -> dict[int, str]:
    """Load optional legacy family members from FAMILY_MEMBERS env."""
    raw_members = os.getenv("FAMILY_MEMBERS", "").strip()
    if not raw_members:
        return {}

    members: dict[int, str] = {}
    for raw_item in raw_members.split(","):
        item = raw_item.strip()
        if not item:
            continue
        if ":" not in item:
            raise ConfigError(
                "FAMILY_MEMBERS must use format chat_id:name,chat_id:name."
            )
        raw_chat_id, raw_name = item.split(":", 1)
        name = raw_name.strip()
        try:
            chat_id = int(raw_chat_id.strip())
        except ValueError as error:
            raise ConfigError("FAMILY_MEMBERS contains invalid chat_id.") from error
        if not name:
            raise ConfigError("FAMILY_MEMBERS contains empty member name.")
        members[chat_id] = name

    if not members:
        raise ConfigError("FAMILY_MEMBERS must contain at least one member.")
    return members


def get_family_members() -> dict[int, str]:
    """Load required legacy family members from FAMILY_MEMBERS env."""
    members = get_configured_family_members()
    if not members:
        raise ConfigError("Environment variable FAMILY_MEMBERS is required.")
    return members


def get_family_chat_ids() -> tuple[int, ...]:
    """Return configured family chat ids."""
    return tuple(get_family_members().keys())


def is_family_chat(chat_id: int) -> bool:
    """Return True when chat id belongs to the configured family."""
    return chat_id in get_family_members()


def get_family_member_name(chat_id: int) -> str:
    """Return configured display name for a family chat id."""
    return get_family_members().get(chat_id, "Участник семьи")


def get_other_family_chat_ids(chat_id: int) -> tuple[int, ...]:
    """Return all family chat ids except the provided one."""
    return tuple(member_id for member_id in get_family_chat_ids() if member_id != chat_id)
