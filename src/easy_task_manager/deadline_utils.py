"""Utilities for parsing and formatting task deadlines."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

MOSCOW_TIMEZONE = ZoneInfo("Europe/Moscow")
DATE_FORMAT = "%d.%m.%Y"
TIME_FORMAT = "%H:%M"
SNOOZE_DEFAULT_TIME = time(9, 0)
SNOOZE_EVENING_TIME = time(18, 0)


def get_today_minsk() -> date:
    """Return current date in the project timezone."""
    return get_today_moscow()


def get_today_moscow() -> date:
    """Return current date in Europe/Moscow timezone."""
    return datetime.now(tz=MOSCOW_TIMEZONE).date()


def get_now_moscow() -> datetime:
    """Return current datetime in Europe/Moscow timezone."""
    return datetime.now(tz=MOSCOW_TIMEZONE)


def get_tomorrow_minsk() -> date:
    """Return tomorrow's date in the project timezone."""
    return get_tomorrow_moscow()


def get_tomorrow_moscow() -> date:
    """Return tomorrow's date in Europe/Moscow timezone."""
    return get_today_moscow() + timedelta(days=1)


def format_deadline_for_user(value: date, deadline_time: time | None = None) -> str:
    """Format deadline for user-facing messages."""
    formatted_date = value.strftime(DATE_FORMAT)
    if deadline_time is None:
        return formatted_date
    return f"{formatted_date} {deadline_time.strftime(TIME_FORMAT)}"


def format_snooze_until_for_user(value: datetime) -> str:
    """Format snooze datetime for user-facing messages."""
    local_value = value.astimezone(MOSCOW_TIMEZONE) if value.tzinfo else value
    return f"{local_value.strftime(DATE_FORMAT)} {local_value.strftime(TIME_FORMAT)}"


def build_snooze_until_for_date(value: date) -> datetime:
    """Build default snooze datetime for a custom date."""
    return datetime.combine(value, SNOOZE_DEFAULT_TIME, tzinfo=MOSCOW_TIMEZONE)


def get_today_evening_snooze(now: datetime | None = None) -> datetime:
    """Return today evening snooze datetime."""
    local_now = (now or get_now_moscow()).astimezone(MOSCOW_TIMEZONE)
    return datetime.combine(local_now.date(), SNOOZE_EVENING_TIME, tzinfo=MOSCOW_TIMEZONE)


def get_tomorrow_snooze(now: datetime | None = None) -> datetime:
    """Return tomorrow morning snooze datetime."""
    local_now = (now or get_now_moscow()).astimezone(MOSCOW_TIMEZONE)
    return datetime.combine(
        local_now.date() + timedelta(days=1),
        SNOOZE_DEFAULT_TIME,
        tzinfo=MOSCOW_TIMEZONE,
    )


def get_weekend_snooze(now: datetime | None = None) -> datetime:
    """Return nearest upcoming Saturday morning snooze datetime."""
    local_now = (now or get_now_moscow()).astimezone(MOSCOW_TIMEZONE)
    days_until_saturday = (5 - local_now.weekday()) % 7
    target_date = local_now.date() + timedelta(days=days_until_saturday)
    candidate = datetime.combine(target_date, SNOOZE_DEFAULT_TIME, tzinfo=MOSCOW_TIMEZONE)
    if candidate <= local_now:
        candidate += timedelta(days=7)
    return candidate


def get_next_week_snooze(now: datetime | None = None) -> datetime:
    """Return morning snooze datetime one week from now."""
    local_now = (now or get_now_moscow()).astimezone(MOSCOW_TIMEZONE)
    return datetime.combine(
        local_now.date() + timedelta(days=7),
        SNOOZE_DEFAULT_TIME,
        tzinfo=MOSCOW_TIMEZONE,
    )


def parse_custom_deadline(text: str) -> date:
    """Parse custom deadline in dd.mm.yyyy format."""
    return datetime.strptime(text.strip(), DATE_FORMAT).date()


def parse_deadline_time(text: str) -> time:
    """Parse custom deadline time in HH:MM format."""
    stripped = text.strip()
    if len(stripped) != 5 or stripped[2] != ":":
        raise ValueError("Time must be in HH:MM format.")
    return datetime.strptime(stripped, TIME_FORMAT).time()


def is_past_deadline(deadline: date, today: date | None = None) -> bool:
    """Check whether deadline is earlier than today."""
    reference_day = today or get_today_moscow()
    return deadline < reference_day


def is_past_deadline_time(
    deadline: date,
    deadline_time: time,
    now: datetime | None = None,
) -> bool:
    """Check whether an exact deadline is earlier than current Moscow time."""
    reference_now = now or datetime.now(tz=MOSCOW_TIMEZONE)
    if reference_now.tzinfo is None:
        local_now = reference_now.replace(tzinfo=MOSCOW_TIMEZONE)
    else:
        local_now = reference_now.astimezone(MOSCOW_TIMEZONE)
    return (deadline, deadline_time) < (local_now.date(), local_now.time())
