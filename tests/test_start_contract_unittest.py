import unittest

from easy_task_manager.start_contract import (
    BOT_MENU_COMMANDS,
    NEW_USER_BUTTONS,
    START_BUTTONS,
    WELCOME_TEXT,
    get_start_response_payload,
    is_manual_start_message,
)


class StartContractTests(unittest.TestCase):
    def test_manual_start_is_detected_case_insensitive(self) -> None:
        self.assertTrue(is_manual_start_message("start"))
        self.assertTrue(is_manual_start_message(" START "))
        self.assertTrue(is_manual_start_message("StArT"))

    def test_manual_start_does_not_match_other_inputs(self) -> None:
        self.assertFalse(is_manual_start_message(None))
        self.assertFalse(is_manual_start_message(""))
        self.assertFalse(is_manual_start_message("/start"))
        self.assertFalse(is_manual_start_message("start now"))

    def test_start_payload_matches_contract(self) -> None:
        payload = get_start_response_payload()

        self.assertEqual(payload["text"], WELCOME_TEXT)
        self.assertEqual(WELCOME_TEXT, "Привет! Я помогаю вести  список дел.")
        self.assertEqual(
            [button.text for button in payload["buttons"]],
            ["Добавить", "Списки", "Семья"],
        )
        self.assertEqual(
            [button.callback_data for button in payload["buttons"]],
            ["todo:add", "todo:lists", "todo:family"],
        )
        self.assertEqual(len(START_BUTTONS), 3)
        self.assertEqual(
            [button.text for button in NEW_USER_BUTTONS],
            ["Присоединиться", "Создать семью"],
        )

    def test_bot_menu_commands_match_main_family_flows(self) -> None:
        self.assertEqual(
            [command.command for command in BOT_MENU_COMMANDS],
            ["menu", "add", "lists", "family", "help"],
        )


if __name__ == "__main__":
    unittest.main()
