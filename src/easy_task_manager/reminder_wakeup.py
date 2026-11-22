"""Wake-up signal for the due-task reminder scheduler."""

from __future__ import annotations

import asyncio
import logging

logger = logging.getLogger(__name__)

_reminder_wakeup_event: asyncio.Event | None = None


def configure_reminder_wakeup(event: asyncio.Event) -> None:
    """Configure the event used to wake the reminder scheduler."""
    global _reminder_wakeup_event
    _reminder_wakeup_event = event


def wake_reminder_scheduler(reason: str) -> None:
    """Wake the reminder scheduler after task data changes."""
    if _reminder_wakeup_event is None:
        logger.info("reminder_scheduler_wakeup_skipped reason=%s", reason)
        return

    _reminder_wakeup_event.set()
    logger.info("reminder_scheduler_wakeup_requested reason=%s", reason)
