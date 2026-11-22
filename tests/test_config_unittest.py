import unittest
from unittest.mock import patch

from easy_task_manager.config import (
    ConfigError,
    get_configured_family_members,
    get_families_file_path,
    get_family_chat_ids,
    get_family_member_name,
    get_family_members,
    get_other_family_chat_ids,
    get_reminder_state_file_path,
    get_task_lists_file_path,
    is_family_chat,
)


class FamilyConfigTests(unittest.TestCase):
    def test_get_family_members_parses_chat_ids_and_names(self) -> None:
        with patch.dict(
            "os.environ",
            {"FAMILY_MEMBERS": "100:Паша, 200:Маша"},
        ):
            self.assertEqual(get_family_members(), {100: "Паша", 200: "Маша"})
            self.assertEqual(get_family_chat_ids(), (100, 200))
            self.assertTrue(is_family_chat(100))
            self.assertFalse(is_family_chat(300))
            self.assertEqual(get_family_member_name(200), "Маша")
            self.assertEqual(get_other_family_chat_ids(100), (200,))

    def test_get_family_members_requires_env(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(ConfigError):
                get_family_members()
            self.assertEqual(get_configured_family_members(), {})

    def test_get_family_members_rejects_invalid_item(self) -> None:
        with patch.dict("os.environ", {"FAMILY_MEMBERS": "100"}):
            with self.assertRaises(ConfigError):
                get_family_members()

    def test_get_reminder_state_file_path_uses_env_override(self) -> None:
        with patch.dict("os.environ", {"REMINDER_STATE_FILE": "custom/state.json"}):
            self.assertEqual(str(get_reminder_state_file_path()), "custom/state.json")

    def test_get_reminder_state_file_path_uses_data_default(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(
                get_reminder_state_file_path().name,
                "reminder_state.json",
            )

    def test_get_families_file_path_uses_env_override(self) -> None:
        with patch.dict("os.environ", {"FAMILIES_FILE": "custom/families.json"}):
            self.assertEqual(str(get_families_file_path()), "custom/families.json")

    def test_get_families_file_path_uses_data_default(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(get_families_file_path().name, "families.json")

    def test_get_task_lists_file_path_uses_env_override(self) -> None:
        with patch.dict("os.environ", {"TASK_LISTS_FILE": "custom/task_lists.json"}):
            self.assertEqual(str(get_task_lists_file_path()), "custom/task_lists.json")

    def test_get_task_lists_file_path_uses_data_default(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(get_task_lists_file_path().name, "task_lists.json")


if __name__ == "__main__":
    unittest.main()
