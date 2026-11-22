"""Telegram WebApp initData validation."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qsl


class WebAppAuthError(RuntimeError):
    """Raised when Telegram WebApp initData cannot be trusted."""


@dataclass(frozen=True)
class WebAppIdentity:
    """Trusted Telegram WebApp identity."""

    chat_id: int
    name: str
    username: str | None = None


def validate_init_data(
    init_data: str,
    bot_token: str,
    max_age_seconds: int = 86400,
) -> WebAppIdentity:
    """Validate Telegram WebApp initData and return the current user."""
    try:
        parsed_pairs = parse_qsl(
            init_data,
            keep_blank_values=True,
            strict_parsing=True,
            max_num_fields=64,
        )
    except ValueError as error:
        raise WebAppAuthError("initData is malformed.") from error
    keys = [key for key, _ in parsed_pairs]
    if len(keys) != len(set(keys)):
        raise WebAppAuthError("initData contains duplicate fields.")
    pairs = dict(parsed_pairs)
    received_hash = pairs.pop("hash", "")
    if not re.fullmatch(r"[0-9a-f]{64}", received_hash):
        raise WebAppAuthError("Missing initData hash.")

    data_check_string = "\n".join(f"{key}={pairs[key]}" for key in sorted(pairs))
    secret_key = hmac.new(
        b"WebAppData",
        bot_token.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    expected_hash = hmac.new(
        secret_key,
        data_check_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected_hash, received_hash):
        raise WebAppAuthError("Invalid initData hash.")

    auth_date = _safe_int(pairs.get("auth_date"))
    if auth_date is None:
        raise WebAppAuthError("Missing auth_date.")
    current_time = int(time.time())
    if auth_date > current_time:
        raise WebAppAuthError("initData auth_date is in the future.")
    if max_age_seconds > 0 and current_time - auth_date > max_age_seconds:
        raise WebAppAuthError("initData is expired.")

    raw_user = pairs.get("user")
    if not raw_user:
        raise WebAppAuthError("Missing user.")
    try:
        user: dict[str, Any] = json.loads(raw_user)
        raw_chat_id = user["id"]
        if isinstance(raw_chat_id, bool) or not isinstance(raw_chat_id, int):
            raise ValueError("user id must be an integer")
        chat_id = raw_chat_id
        if chat_id <= 0:
            raise ValueError("user id must be positive")
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise WebAppAuthError("Invalid user payload.") from error

    name = _display_name(user)
    username = str(user.get("username") or "").strip() or None
    return WebAppIdentity(chat_id=chat_id, name=name, username=username)


def _safe_int(value: object) -> int | None:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


def _display_name(user: dict[str, Any]) -> str:
    full_name = str(user.get("first_name") or "").strip()
    last_name = str(user.get("last_name") or "").strip()
    if last_name:
        full_name = f"{full_name} {last_name}".strip()
    if full_name:
        return full_name
    username = str(user.get("username") or "").strip()
    return username or "Участник семьи"
