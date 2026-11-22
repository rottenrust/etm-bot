"""Utilities for recurring tasks."""

from __future__ import annotations

from calendar import monthrange
from datetime import date, timedelta
from typing import Optional

RECURRENCE_DAILY = "daily"
RECURRENCE_WEEKLY = "weekly"
RECURRENCE_MONTHLY = "monthly"
VALID_RECURRENCES = {
    RECURRENCE_DAILY,
    RECURRENCE_WEEKLY,
    RECURRENCE_MONTHLY,
}

RECURRENCE_LABELS = {
    RECURRENCE_DAILY: "каждый день",
    RECURRENCE_WEEKLY: "каждую неделю",
    RECURRENCE_MONTHLY: "каждый месяц",
}


def normalize_recurrence(value: object) -> Optional[str]:
    """Return a supported recurrence value or None."""
    raw_value = str(value or "").strip()
    if raw_value in VALID_RECURRENCES:
        return raw_value
    return None


def get_recurrence_label(recurrence: Optional[str]) -> str:
    """Return a user-facing recurrence label."""
    normalized = normalize_recurrence(recurrence)
    return RECURRENCE_LABELS.get(normalized, "")


def get_recurrence_anchor_day(
    recurrence: Optional[str],
    deadline: Optional[date],
    anchor_day: Optional[int] = None,
) -> Optional[int]:
    """Return the monthly anchor day for a recurring task."""
    if normalize_recurrence(recurrence) != RECURRENCE_MONTHLY or deadline is None:
        return None
    if anchor_day is not None and 1 <= anchor_day <= 31:
        return anchor_day
    return deadline.day


def calculate_next_deadline(
    deadline: date,
    recurrence: str,
    today: date,
    anchor_day: Optional[int] = None,
) -> Optional[date]:
    """Calculate the next recurring deadline after the current task is done."""
    normalized = normalize_recurrence(recurrence)
    if normalized is None:
        return None

    if normalized == RECURRENCE_DAILY:
        candidate = deadline + timedelta(days=1)
        while candidate <= today:
            candidate += timedelta(days=1)
        return candidate

    if normalized == RECURRENCE_WEEKLY:
        candidate = deadline + timedelta(days=7)
        while candidate <= today:
            candidate += timedelta(days=7)
        return candidate

    monthly_anchor_day = get_recurrence_anchor_day(
        normalized,
        deadline,
        anchor_day=anchor_day,
    )
    if monthly_anchor_day is None:
        return None

    year, month = _next_month(deadline.year, deadline.month)
    candidate = _date_for_month(year=year, month=month, day=monthly_anchor_day)
    while candidate <= today:
        year, month = _next_month(candidate.year, candidate.month)
        candidate = _date_for_month(year=year, month=month, day=monthly_anchor_day)
    return candidate


def _next_month(year: int, month: int) -> tuple[int, int]:
    if month == 12:
        return year + 1, 1
    return year, month + 1


def _date_for_month(year: int, month: int, day: int) -> date:
    return date(year, month, min(day, monthrange(year, month)[1]))
