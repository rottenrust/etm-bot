import hashlib
import hmac
import json
import time
import unittest
from urllib.parse import urlencode, quote

from easy_task_manager.webapp_auth import WebAppAuthError, validate_init_data


class WebAppAuthTests(unittest.TestCase):
    def test_validate_init_data_returns_identity(self) -> None:
        token = "123456:test-token"
        init_data = _build_init_data(
            token=token,
            user={"id": 1001, "first_name": "Паша", "username": "pm"},
        )

        identity = validate_init_data(init_data=init_data, bot_token=token)

        self.assertEqual(identity.chat_id, 1001)
        self.assertEqual(identity.name, "Паша")
        self.assertEqual(identity.username, "pm")

    def test_validate_init_data_rejects_invalid_hash(self) -> None:
        token = "123456:test-token"
        init_data = _build_init_data(
            token=token,
            user={"id": 1001, "first_name": "Паша"},
        )

        with self.assertRaises(WebAppAuthError):
            validate_init_data(init_data=f"{init_data}x", bot_token=token)

    def test_validate_init_data_rejects_duplicate_fields(self) -> None:
        token = "123456:test-token"
        init_data = _build_init_data(token, {"id": 1001, "first_name": "Паша"})

        with self.assertRaises(WebAppAuthError):
            validate_init_data(f"{init_data}&auth_date=1", bot_token=token)

    def test_validate_init_data_rejects_non_ascii_hash_as_auth_error(self) -> None:
        token = "123456:test-token"

        with self.assertRaises(WebAppAuthError):
            validate_init_data(
                "hash=%D0%B0&auth_date=1&user=%7B%7D",
                bot_token=token,
            )

    def test_validate_init_data_rejects_future_and_expired_dates(self) -> None:
        token = "123456:test-token"
        future = _build_init_data(token, {"id": 1001}, auth_date=int(time.time()) + 60)
        expired = _build_init_data(token, {"id": 1001}, auth_date=int(time.time()) - 90000)

        with self.assertRaises(WebAppAuthError):
            validate_init_data(future, bot_token=token)
        with self.assertRaises(WebAppAuthError):
            validate_init_data(expired, bot_token=token)


def _build_init_data(
    token: str,
    user: dict[str, object],
    auth_date: int | None = None,
) -> str:
    pairs = {
        "auth_date": str(auth_date if auth_date is not None else int(time.time())),
        "query_id": "query",
        "user": json.dumps(user, separators=(",", ":"), ensure_ascii=False),
    }
    data_check_string = "\n".join(f"{key}={pairs[key]}" for key in sorted(pairs))
    secret_key = hmac.new(
        b"WebAppData",
        token.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    pairs["hash"] = hmac.new(
        secret_key,
        data_check_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return urlencode(pairs)
