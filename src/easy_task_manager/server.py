"""aiohttp API and static frontend for the Telegram Mini App."""

from __future__ import annotations

import json
import logging
import re
from datetime import date, time
from pathlib import Path
from typing import Any, Optional

from aiohttp import web

from easy_task_manager.config import (
    get_bot_token,
    get_configured_family_members,
    get_families_file_path,
    get_task_lists_file_path,
    get_tasks_file_path,
)
from easy_task_manager.family_storage import JsonFamilyStorage
from easy_task_manager.mini_app_service import (
    MiniAppAccessError,
    MiniAppForbiddenError,
    MiniAppNotFoundError,
    MiniAppService,
    MiniAppUser,
)
from easy_task_manager.task_list_storage import JsonTaskListStorage
from easy_task_manager.task_storage import JsonTaskStorage
from easy_task_manager.webapp_auth import WebAppAuthError, validate_init_data

logger = logging.getLogger(__name__)
SERVICE_KEY = web.AppKey("service", MiniAppService)
BOT_TOKEN_KEY = web.AppKey("bot_token", Optional[str])
STATIC_DIR_KEY = web.AppKey("static_dir", Path)


def create_app(
    *,
    task_storage: Optional[JsonTaskStorage] = None,
    task_list_storage: Optional[JsonTaskListStorage] = None,
    family_storage: Optional[JsonFamilyStorage] = None,
    bot: Any = None,
    bot_token: Optional[str] = None,
    static_dir: Optional[Path] = None,
) -> web.Application:
    """Build the web app; the existing bot process owns its lifecycle."""
    task_storage = task_storage or JsonTaskStorage(get_tasks_file_path())
    task_list_storage = task_list_storage or JsonTaskListStorage(get_task_lists_file_path())
    family_storage = family_storage or JsonFamilyStorage(get_families_file_path())
    task_storage.initialize()
    task_list_storage.initialize()
    family_storage.initialize(default_members=get_configured_family_members())
    service = MiniAppService(
        task_storage=task_storage,
        task_list_storage=task_list_storage,
        family_storage=family_storage,
        bot=bot,
    )
    if static_dir is None:
        static_dir = Path(__file__).resolve().parents[2] / "web" / "dist"

    app = web.Application(
        client_max_size=1024 * 1024,
        middlewares=[_json_api_errors],
    )
    app[SERVICE_KEY] = service
    app[BOT_TOKEN_KEY] = bot_token
    app[STATIC_DIR_KEY] = static_dir

    async def health(_: web.Request) -> web.Response:
        return web.json_response({"status": "ok"})

    async def me(request: web.Request) -> web.Response:
        user = _current_user(request)
        return web.json_response(service.get_me(user))

    async def home(request: web.Request) -> web.Response:
        user = _current_user(request)
        mode = request.query.get("mode", "nearest")
        if mode not in {"nearest", "calendar"}:
            raise web.HTTPBadRequest(text="mode must be nearest or calendar")
        raw_date = request.query.get("date")
        try:
            selected_date = _parse_date(raw_date, "date") if raw_date else None
        except ValueError as error:
            raise web.HTTPBadRequest(text=str(error)) from error
        if mode == "calendar" and selected_date == date.max:
            raise web.HTTPBadRequest(text="date must leave room for the next day")
        return web.json_response(service.get_home(user, mode=mode, selected_date=selected_date))

    async def lists(request: web.Request) -> web.Response:
        user = _current_user(request)
        return web.json_response(service.list_categories(user))

    async def enable_preset(request: web.Request) -> web.Response:
        user = _current_user(request)
        payload = await _json_object(request)
        preset_id = payload.get("presetId")
        if not isinstance(preset_id, str) or not preset_id.strip():
            raise web.HTTPBadRequest(text="presetId is required")
        return web.json_response(service.enable_preset(user, preset_id.strip()))

    async def create_task(request: web.Request) -> web.Response:
        user = _current_user(request)
        payload = _task_payload(await _json_object(request))
        result = await service.create_task(user=user, **payload)
        return web.json_response(result, status=201)

    async def update_task(request: web.Request) -> web.Response:
        user = _current_user(request)
        task_id = _path_id(request, "task_id")
        payload = _task_payload(await _json_object(request))
        return web.json_response(await service.update_task(user=user, task_id=task_id, **payload))

    async def complete_task(request: web.Request) -> web.Response:
        user = _current_user(request)
        task_id = _path_id(request, "task_id")
        return web.json_response(await service.complete_task(user=user, task_id=task_id))

    async def delete_task(request: web.Request) -> web.Response:
        user = _current_user(request)
        task_id = _path_id(request, "task_id")
        return web.json_response(await service.delete_task(user=user, task_id=task_id))

    async def family(request: web.Request) -> web.Response:
        user = _current_user(request)
        return web.json_response(service.get_family(user))

    async def invite(request: web.Request) -> web.Response:
        user = _current_user(request)
        return web.json_response(await service.create_invite(user))

    async def remove_member(request: web.Request) -> web.Response:
        user = _current_user(request)
        chat_id = _path_id(request, "chat_id")
        return web.json_response(await service.remove_family_member(user, chat_id=chat_id))

    async def unknown_api(_: web.Request) -> web.Response:
        return _error(404, "API endpoint not found")

    async def frontend(request: web.Request) -> web.StreamResponse:
        root = request.app[STATIC_DIR_KEY]
        index = root / "index.html"
        if not index.is_file():
            return web.Response(status=503, text="Mini App frontend is not built.")
        requested = (root / request.match_info.get("path", "")).resolve()
        try:
            requested.relative_to(root.resolve())
        except ValueError:
            raise web.HTTPNotFound()
        if requested.is_file():
            return web.FileResponse(requested)
        if request.path.startswith("/assets/"):
            raise web.HTTPNotFound()
        if Path(request.path).suffix:
            raise web.HTTPNotFound()
        return web.FileResponse(index)

    app.router.add_get("/healthz", health)
    app.router.add_get("/api/me", me)
    app.router.add_get("/api/home", home)
    app.router.add_get("/api/lists", lists)
    app.router.add_post("/api/lists", enable_preset)
    app.router.add_post("/api/tasks", create_task)
    app.router.add_patch("/api/tasks/{task_id:\\d+}", update_task)
    app.router.add_post("/api/tasks/{task_id:\\d+}/complete", complete_task)
    app.router.add_delete("/api/tasks/{task_id:\\d+}", delete_task)
    app.router.add_get("/api/family", family)
    app.router.add_post("/api/family/invite", invite)
    app.router.add_delete("/api/family/members/{chat_id:\\d+}", remove_member)
    app.router.add_route("*", "/api", unknown_api)
    app.router.add_route("*", "/api/{tail:.*}", unknown_api)
    app.router.add_get("/{path:.*}", frontend)
    return app


def _current_user(request: web.Request) -> MiniAppUser:
    init_data = request.headers.get("X-Telegram-Init-Data", "").strip()
    if not init_data:
        raise web.HTTPUnauthorized(text="Telegram initData is required")
    try:
        token = request.app[BOT_TOKEN_KEY] or get_bot_token()
        identity = validate_init_data(init_data=init_data, bot_token=token)
    except (WebAppAuthError, RuntimeError) as error:
        raise web.HTTPUnauthorized(text="Telegram initData is invalid or expired") from error
    return MiniAppUser(
        chat_id=identity.chat_id,
        name=identity.name,
        username=identity.username,
    )


@web.middleware
async def _json_api_errors(
    request: web.Request,
    handler: Any,
) -> web.StreamResponse:
    try:
        return await handler(request)
    except web.HTTPException as error:
        if request.path.startswith("/api/") or request.path == "/api":
            return _error(error.status, error.text or error.reason)
        raise
    except MiniAppAccessError as error:
        return _error(403, str(error))
    except MiniAppForbiddenError as error:
        return _error(403, str(error))
    except MiniAppNotFoundError as error:
        return _error(404, str(error))
    except Exception:
        if request.path.startswith("/api/") or request.path == "/api":
            logger.exception("mini_app_api_error path=%s", request.path)
            return _error(500, "Internal server error")
        raise


def _error(status: int, message: str) -> web.Response:
    return web.json_response({"error": message}, status=status)


async def _json_object(request: web.Request) -> dict[str, Any]:
    try:
        value = await request.json()
    except (json.JSONDecodeError, web.HTTPBadRequest, web.HTTPUnsupportedMediaType) as error:
        raise web.HTTPBadRequest(text="A JSON object is required") from error
    if not isinstance(value, dict):
        raise web.HTTPBadRequest(text="A JSON object is required")
    return value


def _task_payload(payload: dict[str, Any]) -> dict[str, Any]:
    text = payload.get("text")
    if not isinstance(text, str) or not text.strip() or len(text.strip()) > 200:
        raise web.HTTPBadRequest(text="text must contain 1 to 200 characters")
    list_id = payload.get("listId", "general")
    if not isinstance(list_id, str) or not re.fullmatch(r"[a-z0-9_-]{1,64}", list_id):
        raise web.HTTPBadRequest(text="listId is invalid")
    try:
        deadline = _parse_date(payload.get("deadline"), "deadline")
        deadline_time = _parse_time(payload.get("deadlineTime"))
    except ValueError as error:
        raise web.HTTPBadRequest(text=str(error)) from error
    note = payload.get("note")
    if note is not None and (not isinstance(note, str) or len(note) > 500):
        raise web.HTTPBadRequest(text="note must be at most 500 characters")
    reminder_enabled = payload.get("reminderEnabled", True)
    if not isinstance(reminder_enabled, bool):
        raise web.HTTPBadRequest(text="reminderEnabled must be boolean")
    if deadline is None and deadline_time is not None:
        raise web.HTTPBadRequest(text="deadlineTime requires a deadline")
    return {
        "text": text.strip(),
        "deadline": deadline,
        "deadline_time": deadline_time,
        "list_id": list_id,
        "note": note.strip() or None if isinstance(note, str) else None,
        "reminder_enabled": reminder_enabled,
    }


def _parse_date(value: Any, field: str) -> Optional[date]:
    if value is None or value == "":
        return None
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError(f"{field} must use YYYY-MM-DD")
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"{field} is invalid") from error


def _parse_time(value: Any) -> Optional[time]:
    if value is None or value == "":
        return None
    if not isinstance(value, str) or not re.fullmatch(r"\d{2}:\d{2}", value):
        raise ValueError("deadlineTime must use HH:MM")
    try:
        return time.fromisoformat(value)
    except ValueError as error:
        raise ValueError("deadlineTime is invalid") from error


def _path_id(request: web.Request, name: str) -> int:
    try:
        value = int(request.match_info[name])
    except (KeyError, ValueError) as error:
        raise web.HTTPBadRequest(text=f"{name} is invalid") from error
    if value <= 0:
        raise web.HTTPBadRequest(text=f"{name} is invalid")
    return value
