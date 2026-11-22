import json
import tempfile
import unittest
from pathlib import Path

from easy_task_manager.family_storage import (
    JOIN_INVITE_ALREADY_MEMBER,
    JOIN_INVITE_INVALID,
    JOIN_INVITE_SUCCESS,
    JOIN_INVITE_USED,
    JsonFamilyStorage,
)


class FamilyStorageTests(unittest.TestCase):
    def test_initialize_seeds_default_family_members(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = JsonFamilyStorage(file_path=Path(temp_dir) / "families.json")

            storage.initialize(default_members={100: "Паша", 200: "Маша"})

            self.assertEqual(storage.get_family_id_for_chat(100), "default")
            self.assertEqual(storage.get_family_id_for_chat(200), "default")
            self.assertEqual(storage.get_member_name(200), "Маша")
            self.assertEqual(storage.list_family_chat_ids("default"), (100, 200))
            self.assertEqual(storage.get_family_owner_chat_id("default"), 100)

    def test_create_family_for_new_member_keeps_family_isolated(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = JsonFamilyStorage(file_path=Path(temp_dir) / "families.json")
            storage.initialize(default_members={100: "Паша"})

            member = storage.create_family_for_member(chat_id=300, name="Ира")

            self.assertNotEqual(member.family_id, "default")
            self.assertEqual(storage.list_family_chat_ids(member.family_id), (300,))
            self.assertEqual(storage.list_family_chat_ids("default"), (100,))
            self.assertEqual(storage.get_family_owner_chat_id(member.family_id), 300)

    def test_invite_adds_new_member_to_inviter_family_once(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = JsonFamilyStorage(file_path=Path(temp_dir) / "families.json")
            storage.initialize(default_members={100: "Паша"})
            invite = storage.create_invite(created_by_chat_id=100)
            self.assertIsNotNone(invite)

            status, member = storage.join_family_by_invite(
                chat_id=200,
                name="Маша",
                code=invite.code.lower(),
            )
            second_status, second_member = storage.join_family_by_invite(
                chat_id=300,
                name="Ира",
                code=invite.code,
            )

            self.assertEqual(status, JOIN_INVITE_SUCCESS)
            self.assertIsNotNone(member)
            self.assertEqual(member.family_id, "default")
            self.assertEqual(storage.list_family_chat_ids("default"), (100, 200))
            self.assertEqual(second_status, JOIN_INVITE_USED)
            self.assertIsNone(second_member)

    def test_invalid_invite_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = JsonFamilyStorage(file_path=Path(temp_dir) / "families.json")
            storage.initialize(default_members={100: "Паша"})

            status, member = storage.join_family_by_invite(
                chat_id=200,
                name="Маша",
                code="NOPE",
            )

            self.assertEqual(status, JOIN_INVITE_INVALID)
            self.assertIsNone(member)

    def test_existing_member_is_not_moved_by_invite(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = JsonFamilyStorage(file_path=Path(temp_dir) / "families.json")
            storage.initialize(default_members={100: "Паша"})
            member = storage.create_family_for_member(chat_id=200, name="Маша")
            invite = storage.create_invite(created_by_chat_id=100)

            status, returned_member = storage.join_family_by_invite(
                chat_id=200,
                name="Маша",
                code=invite.code,
            )

            self.assertEqual(status, JOIN_INVITE_ALREADY_MEMBER)
            self.assertEqual(returned_member.family_id, member.family_id)
            self.assertNotEqual(storage.get_family_id_for_chat(200), "default")

    def test_delete_family_removes_members_and_invites_only_for_that_family(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = JsonFamilyStorage(file_path=Path(temp_dir) / "families.json")
            storage.initialize(default_members={100: "Паша"})
            member = storage.create_family_for_member(chat_id=200, name="Маша")
            invite_default = storage.create_invite(created_by_chat_id=100)
            invite_other = storage.create_invite(created_by_chat_id=200)

            deleted_chat_ids = storage.delete_family(member.family_id)

            self.assertEqual(deleted_chat_ids, (200,))
            self.assertIsNone(storage.get_family_id_for_chat(200))
            self.assertEqual(storage.get_family_id_for_chat(100), "default")
            self.assertEqual(
                storage.join_family_by_invite(300, "Ира", invite_other.code)[0],
                JOIN_INVITE_INVALID,
            )
            self.assertEqual(
                storage.join_family_by_invite(301, "Оля", invite_default.code)[0],
                JOIN_INVITE_SUCCESS,
            )

    def test_delete_default_family_prevents_reinitialize_from_env_members(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "families.json"
            storage = JsonFamilyStorage(file_path=file_path)
            storage.initialize(default_members={100: "Паша", 200: "Маша"})

            deleted_chat_ids = storage.delete_family("default")
            storage.initialize(default_members={100: "Паша", 200: "Маша"})

            self.assertEqual(deleted_chat_ids, (100, 200))
            self.assertTrue(storage.is_family_deleted("default"))
            self.assertIsNone(storage.get_family_id_for_chat(100))
            self.assertEqual(storage.list_family_chat_ids("default"), ())
            with file_path.open("r", encoding="utf-8") as source:
                raw = json.load(source)
            default_family = next(family for family in raw["families"] if family["id"] == "default")
            self.assertIsNotNone(default_family.get("deleted_at"))

    def test_delete_unknown_family_does_not_change_existing_members(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = JsonFamilyStorage(file_path=Path(temp_dir) / "families.json")
            storage.initialize(default_members={100: "Паша"})

            deleted_chat_ids = storage.delete_family("missing")

            self.assertEqual(deleted_chat_ids, ())
            self.assertEqual(storage.get_family_id_for_chat(100), "default")

    def test_existing_member_names_are_not_rewritten_on_initialize(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = JsonFamilyStorage(file_path=Path(temp_dir) / "families.json")
            storage.initialize(default_members={100: "Паша"})

            storage.initialize(default_members={100: "pasha_username", 200: "Маша"})

            self.assertEqual(storage.get_member_name(100), "Паша")
            self.assertEqual(storage.get_member_name(200), "Маша")

    def test_remove_member_removes_only_that_member(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = JsonFamilyStorage(file_path=Path(temp_dir) / "families.json")
            storage.initialize(default_members={100: "Паша", 200: "Маша", 300: "Ира"})

            removed = storage.remove_member(family_id="default", chat_id=200)

            self.assertIsNotNone(removed)
            self.assertEqual(removed.name, "Маша")
            self.assertEqual(storage.list_family_chat_ids("default"), (100, 300))
            self.assertIsNone(storage.get_family_id_for_chat(200))

    def test_removed_legacy_member_is_not_restored_after_restart(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = JsonFamilyStorage(file_path=Path(temp_dir) / "families.json")
            configured_members = {100: "Паша", 200: "Маша"}
            storage.initialize(default_members=configured_members)

            storage.remove_member(family_id="default", chat_id=200)
            storage.initialize(default_members=configured_members)

            self.assertIsNone(storage.get_family_id_for_chat(200))
            self.assertEqual(storage.list_family_chat_ids("default"), (100,))
            raw = json.loads(storage.file_path.read_text(encoding="utf-8"))
            removed = next(member for member in raw["members"] if member["chat_id"] == 200)
            self.assertTrue(removed.get("removed_at"))


if __name__ == "__main__":
    unittest.main()
