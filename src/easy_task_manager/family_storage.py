"""JSON storage for families, members, and invite codes."""

from __future__ import annotations

import json
import secrets
import string
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from easy_task_manager.task_storage import DEFAULT_FAMILY_ID

INVITE_CODE_LENGTH = 8
INVITE_CODE_ALPHABET = string.ascii_uppercase + string.digits

JOIN_INVITE_SUCCESS = "success"
JOIN_INVITE_INVALID = "invalid"
JOIN_INVITE_USED = "used"
JOIN_INVITE_ALREADY_MEMBER = "already_member"


@dataclass(frozen=True)
class FamilyMember:
    """A Telegram private chat attached to a family."""

    chat_id: int
    family_id: str
    name: str
    joined_at: datetime
    removed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "chat_id": self.chat_id,
            "family_id": self.family_id,
            "name": self.name,
            "joined_at": self.joined_at.isoformat(),
        }
        if self.removed_at is not None:
            result["removed_at"] = self.removed_at.isoformat()
        return result


@dataclass(frozen=True)
class FamilyInvite:
    """Single-use family invite code."""

    code: str
    family_id: str
    created_by_chat_id: int
    created_at: datetime
    used_at: Optional[datetime] = None
    used_by_chat_id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "family_id": self.family_id,
            "created_by_chat_id": self.created_by_chat_id,
            "created_at": self.created_at.isoformat(),
            "used_at": self.used_at.isoformat() if self.used_at else None,
            "used_by_chat_id": self.used_by_chat_id,
        }


class JsonFamilyStorage:
    """Small JSON storage for public bot family membership."""

    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path

    def initialize(self, default_members: dict[int, str] | None = None) -> None:
        """Create storage and seed configured legacy family members."""
        data = self._read_data()
        changed = False
        default_owner_chat_id = next(iter(default_members or {}), None)

        if self._is_family_deleted(data=data, family_id=DEFAULT_FAMILY_ID):
            if not self.file_path.exists():
                self._write_data(data)
            return

        default_family = self._find_raw_family(data=data, family_id=DEFAULT_FAMILY_ID)
        if default_family is None:
            default_family = {
                "id": DEFAULT_FAMILY_ID,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            if default_owner_chat_id is not None:
                default_family["owner_chat_id"] = default_owner_chat_id
            data["families"].append(
                default_family
            )
            changed = True

        for chat_id, name in (default_members or {}).items():
            if self._find_raw_member(data=data, chat_id=chat_id) is not None or any(
                (member := _member_from_dict(raw)) is not None
                and member.chat_id == chat_id
                and member.removed_at is not None
                for raw in data["members"]
            ):
                continue
            member = FamilyMember(
                chat_id=chat_id,
                family_id=DEFAULT_FAMILY_ID,
                name=name,
                joined_at=datetime.now(timezone.utc),
            )
            data["members"].append(member.to_dict())
            changed = True

        if self._ensure_family_owner(data=data, family_id=DEFAULT_FAMILY_ID):
            changed = True

        if changed or not self.file_path.exists():
            self._write_data(data)

    def get_member(self, chat_id: int) -> Optional[FamilyMember]:
        data = self._read_data()
        raw_member = self._find_raw_member(data=data, chat_id=chat_id)
        if raw_member is None:
            return None
        member = _member_from_dict(raw_member)
        if (
            member is None
            or member.removed_at is not None
            or self._is_family_deleted(data=data, family_id=member.family_id)
        ):
            return None
        return member

    def get_family_id_for_chat(self, chat_id: int) -> Optional[str]:
        member = self.get_member(chat_id=chat_id)
        return member.family_id if member else None

    def is_family_deleted(self, family_id: str) -> bool:
        return self._is_family_deleted(data=self._read_data(), family_id=family_id)

    def get_member_name(self, chat_id: int) -> str:
        member = self.get_member(chat_id=chat_id)
        if member is None:
            return "Участник семьи"
        return member.name

    def list_family_chat_ids(self, family_id: str) -> tuple[int, ...]:
        data = self._read_data()
        if self._is_family_deleted(data=data, family_id=family_id):
            return ()

        members = data["members"]
        chat_ids: list[int] = []
        for raw_member in members:
            member = _member_from_dict(raw_member)
            if member is not None and member.removed_at is None and member.family_id == family_id:
                chat_ids.append(member.chat_id)
        return tuple(chat_ids)

    def list_family_members(self, family_id: str) -> tuple[FamilyMember, ...]:
        data = self._read_data()
        if self._is_family_deleted(data=data, family_id=family_id):
            return ()

        members: list[FamilyMember] = []
        for raw_member in data["members"]:
            member = _member_from_dict(raw_member)
            if member is not None and member.removed_at is None and member.family_id == family_id:
                members.append(member)
        return tuple(sorted(members, key=lambda member: member.joined_at))

    def list_other_family_chat_ids(
        self,
        family_id: str,
        actor_chat_id: int,
    ) -> tuple[int, ...]:
        return tuple(
            chat_id
            for chat_id in self.list_family_chat_ids(family_id=family_id)
            if chat_id != actor_chat_id
        )

    def get_family_owner_chat_id(self, family_id: str) -> Optional[int]:
        data = self._read_data()
        if self._is_family_deleted(data=data, family_id=family_id):
            return None
        if self._ensure_family_owner(data=data, family_id=family_id):
            self._write_data(data)
        raw_family = self._find_raw_family(data=data, family_id=family_id)
        if raw_family is None:
            return None
        try:
            return int(raw_family["owner_chat_id"])
        except (KeyError, TypeError, ValueError):
            return None

    def create_family_for_member(self, chat_id: int, name: str) -> FamilyMember:
        existing = self.get_member(chat_id=chat_id)
        if existing is not None:
            return existing

        data = self._read_data()
        family_id = self._generate_family_id(data=data)
        now = datetime.now(timezone.utc)
        data["families"].append(
            {
                "id": family_id,
                "created_at": now.isoformat(),
                "owner_chat_id": chat_id,
            }
        )
        member = FamilyMember(
            chat_id=chat_id,
            family_id=family_id,
            name=name,
            joined_at=now,
        )
        data["members"].append(member.to_dict())
        self._write_data(data)
        return member

    def remove_member(self, family_id: str, chat_id: int) -> Optional[FamilyMember]:
        data = self._read_data()
        if self._is_family_deleted(data=data, family_id=family_id):
            return None

        removed_member: Optional[FamilyMember] = None
        now = datetime.now(timezone.utc)
        for raw_member in data["members"]:
            member = _member_from_dict(raw_member)
            if (
                member is not None
                and member.removed_at is None
                and member.family_id == family_id
                and member.chat_id == chat_id
            ):
                removed_member = member
                raw_member["removed_at"] = now.isoformat()

        if removed_member is None:
            return None

        self._write_data(data)
        return removed_member

    def create_invite(self, created_by_chat_id: int) -> Optional[FamilyInvite]:
        member = self.get_member(chat_id=created_by_chat_id)
        if member is None:
            return None

        data = self._read_data()
        code = self._generate_invite_code(data=data)
        invite = FamilyInvite(
            code=code,
            family_id=member.family_id,
            created_by_chat_id=created_by_chat_id,
            created_at=datetime.now(timezone.utc),
        )
        data["invites"].append(invite.to_dict())
        self._write_data(data)
        return invite

    def delete_family(self, family_id: str) -> tuple[int, ...]:
        data = self._read_data()
        deleted_member_chat_ids = tuple(
            member.chat_id
            for raw_member in data["members"]
            if (member := _member_from_dict(raw_member)) is not None
            and member.removed_at is None
            and member.family_id == family_id
        )
        now = datetime.now(timezone.utc).isoformat()

        data["members"] = [
            raw_member
            for raw_member in data["members"]
            if (
                (member := _member_from_dict(raw_member)) is None
                or member.family_id != family_id
            )
        ]
        data["invites"] = [
            raw_invite
            for raw_invite in data["invites"]
            if (
                (invite := _invite_from_dict(raw_invite)) is None
                or invite.family_id != family_id
            )
        ]

        if family_id == DEFAULT_FAMILY_ID:
            default_family = self._find_raw_family(data=data, family_id=family_id)
            if default_family is None:
                default_family = {"id": family_id, "created_at": now}
                data["families"].append(default_family)
            default_family["deleted_at"] = now
        else:
            data["families"] = [
                raw_family
                for raw_family in data["families"]
                if str(raw_family.get("id")) != family_id
            ]

        self._write_data(data)
        return deleted_member_chat_ids

    def join_family_by_invite(
        self,
        chat_id: int,
        name: str,
        code: str,
    ) -> tuple[str, Optional[FamilyMember]]:
        if self.get_member(chat_id=chat_id) is not None:
            return JOIN_INVITE_ALREADY_MEMBER, self.get_member(chat_id=chat_id)

        normalized_code = _normalize_invite_code(code)
        if not normalized_code:
            return JOIN_INVITE_INVALID, None

        data = self._read_data()
        for raw_invite in data["invites"]:
            invite = _invite_from_dict(raw_invite)
            if invite is None or invite.code != normalized_code:
                continue
            if self._is_family_deleted(data=data, family_id=invite.family_id):
                return JOIN_INVITE_INVALID, None
            if invite.used_at is not None:
                return JOIN_INVITE_USED, None

            now = datetime.now(timezone.utc)
            raw_invite["used_at"] = now.isoformat()
            raw_invite["used_by_chat_id"] = chat_id
            member = FamilyMember(
                chat_id=chat_id,
                family_id=invite.family_id,
                name=name,
                joined_at=now,
            )
            data["members"].append(member.to_dict())
            self._write_data(data)
            return JOIN_INVITE_SUCCESS, member

        return JOIN_INVITE_INVALID, None

    def _generate_family_id(self, data: Dict[str, List[Dict[str, Any]]]) -> str:
        existing_ids = {str(family.get("id")) for family in data["families"]}
        while True:
            family_id = f"family_{secrets.token_urlsafe(8)}"
            if family_id not in existing_ids:
                return family_id

    def _generate_invite_code(self, data: Dict[str, List[Dict[str, Any]]]) -> str:
        existing_codes = {str(invite.get("code")) for invite in data["invites"]}
        while True:
            code = "".join(secrets.choice(INVITE_CODE_ALPHABET) for _ in range(INVITE_CODE_LENGTH))
            if code not in existing_codes:
                return code

    def _read_data(self) -> Dict[str, List[Dict[str, Any]]]:
        if not self.file_path.exists():
            return {"families": [], "members": [], "invites": []}

        with self.file_path.open("r", encoding="utf-8") as source:
            loaded = json.load(source)
        if not isinstance(loaded, dict):
            return {"families": [], "members": [], "invites": []}

        return {
            "families": _dict_list(loaded.get("families")),
            "members": _dict_list(loaded.get("members")),
            "invites": _dict_list(loaded.get("invites")),
        }

    def _write_data(self, data: Dict[str, List[Dict[str, Any]]]) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        with self.file_path.open("w", encoding="utf-8") as destination:
            json.dump(data, destination, ensure_ascii=False, indent=2)

    @staticmethod
    def _find_raw_family(
        data: Dict[str, List[Dict[str, Any]]],
        family_id: str,
    ) -> Optional[Dict[str, Any]]:
        for raw_family in data["families"]:
            if str(raw_family.get("id")) == family_id:
                return raw_family
        return None

    @classmethod
    def _is_family_deleted(
        cls,
        data: Dict[str, List[Dict[str, Any]]],
        family_id: str,
    ) -> bool:
        raw_family = cls._find_raw_family(data=data, family_id=family_id)
        return raw_family is not None and bool(raw_family.get("deleted_at"))

    @staticmethod
    def _find_raw_member(
        data: Dict[str, List[Dict[str, Any]]],
        chat_id: int,
    ) -> Optional[Dict[str, Any]]:
        for raw_member in data["members"]:
            try:
                if int(raw_member.get("chat_id")) == chat_id and not raw_member.get("removed_at"):
                    return raw_member
            except (TypeError, ValueError):
                continue
        return None

    @classmethod
    def _ensure_family_owner(
        cls,
        data: Dict[str, List[Dict[str, Any]]],
        family_id: str,
    ) -> bool:
        raw_family = cls._find_raw_family(data=data, family_id=family_id)
        if raw_family is None or raw_family.get("owner_chat_id") is not None:
            return False

        family_members: list[FamilyMember] = []
        for raw_member in data["members"]:
            member = _member_from_dict(raw_member)
            if member is not None and member.removed_at is None and member.family_id == family_id:
                family_members.append(member)
        if not family_members:
            return False

        owner = min(family_members, key=lambda member: member.joined_at)
        raw_family["owner_chat_id"] = owner.chat_id
        return True


def _normalize_invite_code(code: str) -> str:
    return code.strip().upper()


def _dict_list(value: object) -> List[Dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _member_from_dict(raw: Dict[str, Any]) -> Optional[FamilyMember]:
    try:
        return FamilyMember(
            chat_id=int(raw["chat_id"]),
            family_id=str(raw["family_id"]),
            name=str(raw["name"]),
            joined_at=datetime.fromisoformat(str(raw["joined_at"])),
            removed_at=datetime.fromisoformat(str(raw["removed_at"]))
            if raw.get("removed_at")
            else None,
        )
    except (KeyError, TypeError, ValueError):
        return None


def _invite_from_dict(raw: Dict[str, Any]) -> Optional[FamilyInvite]:
    try:
        raw_used_at = raw.get("used_at")
        raw_used_by_chat_id = raw.get("used_by_chat_id")
        return FamilyInvite(
            code=str(raw["code"]),
            family_id=str(raw["family_id"]),
            created_by_chat_id=int(raw["created_by_chat_id"]),
            created_at=datetime.fromisoformat(str(raw["created_at"])),
            used_at=datetime.fromisoformat(str(raw_used_at)) if raw_used_at else None,
            used_by_chat_id=int(raw_used_by_chat_id)
            if raw_used_by_chat_id is not None
            else None,
        )
    except (KeyError, TypeError, ValueError):
        return None
