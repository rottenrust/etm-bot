from easy_task_manager.start_contract import (
    NEW_USER_BUTTONS,
    START_BUTTONS,
    WELCOME_TEXT,
    get_start_response_payload,
    is_cancel_message,
    is_manual_start_message,
)


def test_manual_start_is_detected_case_insensitive() -> None:
    assert is_manual_start_message("start")
    assert is_manual_start_message(" START ")
    assert is_manual_start_message("StArT")


def test_manual_start_does_not_match_other_inputs() -> None:
    assert not is_manual_start_message(None)
    assert not is_manual_start_message("")
    assert not is_manual_start_message("/start")
    assert not is_manual_start_message("start now")


def test_cancel_is_detected_case_insensitive() -> None:
    assert is_cancel_message("отмена")
    assert is_cancel_message(" Отмена ")
    assert is_cancel_message("ОТМЕНА")


def test_cancel_does_not_match_other_inputs() -> None:
    assert not is_cancel_message(None)
    assert not is_cancel_message("")
    assert not is_cancel_message("отменить")
    assert not is_cancel_message("отмена задачи")


def test_start_payload_matches_contract() -> None:
    payload = get_start_response_payload()

    assert payload["text"] == WELCOME_TEXT
    assert WELCOME_TEXT == "Привет! Я помогаю вести  список дел."
    assert [button.text for button in payload["buttons"]] == [
        "Добавить",
        "Списки",
        "Семья",
    ]
    assert [button.callback_data for button in payload["buttons"]] == [
        "todo:add",
        "todo:lists",
        "todo:family",
    ]
    assert len(START_BUTTONS) == 3
    assert [button.text for button in NEW_USER_BUTTONS] == [
        "Присоединиться",
        "Создать семью",
    ]
