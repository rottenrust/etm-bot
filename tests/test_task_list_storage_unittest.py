import json
import tempfile
import unittest
from pathlib import Path

from easy_task_manager.task_list_storage import (
    DEFAULT_TASK_LIST_ID,
    JsonTaskListStorage,
    TASK_LIST_PRESETS,
)


class JsonTaskListStorageTests(unittest.TestCase):
    def test_initialize_creates_empty_task_lists_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "data" / "task_lists.json"
            storage = JsonTaskListStorage(file_path=file_path)

            storage.initialize()

            self.assertTrue(file_path.exists())
            with file_path.open("r", encoding="utf-8") as source:
                raw = json.load(source)
            self.assertEqual(raw, [])

    def test_ensure_default_task_list_creates_general_for_family(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "task_lists.json"
            storage = JsonTaskListStorage(file_path=file_path)

            task_list = storage.ensure_default_task_list(family_id="family-1")

            self.assertEqual(task_list.id, DEFAULT_TASK_LIST_ID)
            self.assertEqual(task_list.family_id, "family-1")
            self.assertEqual(task_list.title, "Общий")
            self.assertEqual(storage.list_task_lists_by_family("family-1"), [task_list])

    def test_create_task_list_from_preset_does_not_duplicate_existing_list(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "task_lists.json"
            storage = JsonTaskListStorage(file_path=file_path)

            first = storage.create_task_list_from_preset(
                family_id="family-1",
                preset_id="shopping",
            )
            second = storage.create_task_list_from_preset(
                family_id="family-1",
                preset_id="shopping",
            )

            self.assertIsNotNone(first)
            self.assertEqual(first, second)
            task_lists = storage.list_task_lists_by_family(family_id="family-1")
            self.assertEqual([task_list.id for task_list in task_lists], ["general", "shopping"])

    def test_list_task_lists_by_family_filters_other_families(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "task_lists.json"
            storage = JsonTaskListStorage(file_path=file_path)
            storage.create_task_list_from_preset(family_id="family-1", preset_id="shopping")
            storage.create_task_list_from_preset(family_id="family-2", preset_id="home")

            task_lists = storage.list_task_lists_by_family(family_id="family-1")

            self.assertEqual([task_list.id for task_list in task_lists], ["general", "shopping"])

    def test_unknown_preset_is_not_created(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "task_lists.json"
            storage = JsonTaskListStorage(file_path=file_path)

            task_list = storage.create_task_list_from_preset(
                family_id="family-1",
                preset_id="unknown",
            )

            self.assertIsNone(task_list)
            self.assertEqual(storage.list_task_lists_by_family("family-1")[0].id, "general")

    def test_work_preset_is_available(self) -> None:
        self.assertIn(
            ("work", "Работа"),
            [(preset.id, preset.title) for preset in TASK_LIST_PRESETS],
        )


if __name__ == "__main__":
    unittest.main()
