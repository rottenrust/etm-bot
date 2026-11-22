"""Start-event contracts shared across handlers and tests."""

from dataclasses import dataclass
from typing import Dict, List, Optional

WELCOME_TEXT = "Привет! Я помогаю вести  список дел."
UNKNOWN_USER_TEXT = "Этот семейный список доступен только участникам семьи."
NEW_USER_TEXT = "Привет! Что хочешь сделать?"
HELP_TEXT = (
    "Я помогаю вести семейный список дел.\n"
    "/menu — открыть главное меню\n"
    "/add — добавить дело\n"
    "/lists — открыть списки дел\n"
    "/family — семейные настройки"
)
FAMILY_CREATED_TEXT = "Готово, я создал для тебя отдельный семейный список."
FAMILY_MENU_TEXT = "Что сделать с семейным списком?"
FAMILY_DELETE_CONFIRM_TEXT = (
    "Удалить семейный список? Все дела, участники и приглашения будут удалены."
)
FAMILY_DELETE_CANCELLED_TEXT = "Удаление отменено."
FAMILY_DELETED_TEXT = "Семейный список удален."
FAMILY_MEMBERS_TEXT = "Участники семьи:"
FAMILY_MEMBERS_NO_REMOVABLE_TEXT = "Других участников пока нет."
FAMILY_MEMBER_REMOVE_FORBIDDEN_TEXT = "Удалять участников может только создатель семьи."
FAMILY_MEMBER_REMOVE_SELF_TEXT = "Себя удалить нельзя."
FAMILY_MEMBER_REMOVE_CONFIRM_TEMPLATE = "Удалить {name} из семейного списка?"
FAMILY_MEMBER_REMOVED_TEXT_TEMPLATE = "{name}: удален из семейного списка"
FAMILY_MEMBER_JOINED_TEXT_TEMPLATE = "{name}: присоединился к семейному списку"
FAMILY_MEMBER_REMOVE_CANCELLED_TEXT = "Удаление участника отменено."
JOIN_FAMILY_PROMPT_TEXT = "Отправь код приглашения, который тебе прислали."
JOIN_FAMILY_SUCCESS_TEXT = "Готово, ты присоединился к семейному списку."
JOIN_FAMILY_INVALID_TEXT = "Код не подошел. Проверь его и отправь еще раз."
JOIN_FAMILY_USED_TEXT = "Этот код уже использован. Попроси новый код приглашения."
ALREADY_IN_FAMILY_TEXT = "Ты уже подключен к семейному списку."
INVITE_UNAVAILABLE_TEXT = "Сначала создай семью или присоединись к существующей."
INVITE_TEXT_TEMPLATE = (
    "Код приглашения: {code}\n"
    "Отправь его человеку, которого хочешь добавить в семейный список."
)
INVITE_TEXT_WITH_LINK_TEMPLATE = (
    "Код приглашения: {code}\n"
    "Можно отправить код или ссылку: {link}"
)
ADD_TASK_CALLBACK_DATA = "todo:add"
LIST_TASKS_CALLBACK_DATA = "todo:list"
TASK_LISTS_CALLBACK_DATA = "todo:lists"
INVITE_CALLBACK_DATA = "todo:invite"
FAMILY_MENU_CALLBACK_DATA = "todo:family"
FAMILY_MEMBERS_CALLBACK_DATA = "todo:family:members"
DELETE_FAMILY_CALLBACK_DATA = "todo:family:delete"
CONFIRM_DELETE_FAMILY_CALLBACK_DATA = "todo:family:delete:confirm"
CANCEL_DELETE_FAMILY_CALLBACK_DATA = "todo:family:delete:cancel"
REMOVE_FAMILY_MEMBER_CALLBACK_PREFIX = "todo:family:member:remove:"
CONFIRM_REMOVE_FAMILY_MEMBER_CALLBACK_PREFIX = "todo:family:member:remove:confirm:"
CANCEL_REMOVE_FAMILY_MEMBER_CALLBACK_DATA = "todo:family:member:remove:cancel"
BACK_TO_START_CALLBACK_DATA = "todo:back:start"
CREATE_FAMILY_CALLBACK_DATA = "todo:family:create"
JOIN_FAMILY_CALLBACK_DATA = "todo:family:join"


@dataclass(frozen=True)
class StartButton:
    text: str
    callback_data: str


@dataclass(frozen=True)
class BotMenuCommand:
    command: str
    description: str


BOT_MENU_COMMANDS = (
    BotMenuCommand(command="menu", description="Открыть меню"),
    BotMenuCommand(command="add", description="Добавить дело"),
    BotMenuCommand(command="lists", description="Списки дел"),
    BotMenuCommand(command="family", description="Семейные настройки"),
    BotMenuCommand(command="help", description="Помощь"),
)


START_BUTTONS = (
    StartButton(text="Добавить", callback_data=ADD_TASK_CALLBACK_DATA),
    StartButton(text="Списки", callback_data=TASK_LISTS_CALLBACK_DATA),
    StartButton(text="Семья", callback_data=FAMILY_MENU_CALLBACK_DATA),
)

NEW_USER_BUTTONS = (
    StartButton(text="Присоединиться", callback_data=JOIN_FAMILY_CALLBACK_DATA),
    StartButton(text="Создать семью", callback_data=CREATE_FAMILY_CALLBACK_DATA),
)

FAMILY_MENU_BUTTONS = (
    StartButton(text="Пригласить", callback_data=INVITE_CALLBACK_DATA),
    StartButton(text="Участники", callback_data=FAMILY_MEMBERS_CALLBACK_DATA),
    StartButton(text="Удалить семью", callback_data=DELETE_FAMILY_CALLBACK_DATA),
    StartButton(text="Назад", callback_data=BACK_TO_START_CALLBACK_DATA),
)

FAMILY_DELETE_CONFIRM_BUTTONS = (
    StartButton(text="Да, удалить", callback_data=CONFIRM_DELETE_FAMILY_CALLBACK_DATA),
    StartButton(text="Отмена", callback_data=CANCEL_DELETE_FAMILY_CALLBACK_DATA),
)


def is_manual_start_message(text: Optional[str]) -> bool:
    """Check if a text message should be treated as a manual start event."""
    if text is None:
        return False
    return text.strip().lower() == "start"


def is_cancel_message(text: Optional[str]) -> bool:
    """Check if a text message should cancel the current flow."""
    if text is None:
        return False
    return text.strip().lower() == "отмена"


def get_start_response_payload() -> Dict[str, object]:
    """Return immutable contract for welcome message and inline buttons."""
    return {
        "text": WELCOME_TEXT,
        "buttons": list(START_BUTTONS),
    }
