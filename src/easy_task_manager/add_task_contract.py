"""Contracts for add-task flow."""

ASK_TASK_TEXT = "Напиши, что добавить"
TASK_ADDED_TEMPLATE = "Добавил задачу: {task_text}"
ASK_DEADLINE_TEXT = "Установим дедлайн для задачи?"
CUSTOM_DEADLINE_PROMPT_TEXT = "Укажи дату в формате дд.мм.гггг"
CUSTOM_DEADLINE_INVALID_TEXT = (
    "Не получилось распознать дату. Введи дедлайн в формате дд.мм.гггг "
    "и не раньше сегодняшнего дня."
)
ASK_DEADLINE_TIME_TEXT = "Укажи время дедлайна в формате чч:мм или пропусти"
CUSTOM_DEADLINE_TIME_INVALID_TEXT = (
    "Не получилось распознать время. Введи время в формате чч:мм "
    "и не раньше текущего времени."
)
DEADLINE_ADDED_TEXT = "И дедлайн тоже добавил!"
DEADLINE_TIME_ADDED_TEXT = "И время указал!"
DEADLINE_SKIPPED_TEXT = "Дедлайн не добавляем!"
ASK_RECURRENCE_TEXT = "Повторять задачу?"
RECURRENCE_SKIPPED_TEXT = "Не повторяем."
RECURRENCE_ADDED_TEMPLATE = "Буду повторять: {recurrence_label}"

DEADLINE_TODAY_CALLBACK = "todo:deadline:today"
DEADLINE_TOMORROW_CALLBACK = "todo:deadline:tomorrow"
DEADLINE_SKIP_CALLBACK = "todo:deadline:skip"
DEADLINE_CUSTOM_CALLBACK = "todo:deadline:custom"
DEADLINE_TIME_SKIP_CALLBACK = "todo:deadline_time:skip"
RECURRENCE_DAILY_CALLBACK = "todo:recurrence:daily"
RECURRENCE_WEEKLY_CALLBACK = "todo:recurrence:weekly"
RECURRENCE_MONTHLY_CALLBACK = "todo:recurrence:monthly"
RECURRENCE_SKIP_CALLBACK = "todo:recurrence:skip"

DEADLINE_BUTTONS = (
    ("Сегодня", DEADLINE_TODAY_CALLBACK),
    ("Завтра", DEADLINE_TOMORROW_CALLBACK),
    ("Пропустить", DEADLINE_SKIP_CALLBACK),
    ("Свой дедлайн", DEADLINE_CUSTOM_CALLBACK),
)

DEADLINE_TIME_BUTTONS = (("Пропустить", DEADLINE_TIME_SKIP_CALLBACK),)

RECURRENCE_BUTTONS = (
    ("Каждый день", RECURRENCE_DAILY_CALLBACK),
    ("Каждую неделю", RECURRENCE_WEEKLY_CALLBACK),
    ("Каждый месяц", RECURRENCE_MONTHLY_CALLBACK),
    ("Не повторять", RECURRENCE_SKIP_CALLBACK),
)
