"""Shared timestamp helpers for local calendar dates and UTC retention."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Optional


def now_local_iso() -> str:
    """Return an ISO timestamp whose date and offset represent the device locale."""
    return datetime.now().astimezone().isoformat()


def parse_timestamp(value: str) -> datetime:
    normalized = str(value or "").strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    parsed = datetime.fromisoformat(normalized)
    # Legacy Gumli timestamps without an offset were produced with utcnow().
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def history_timestamp(item) -> str:
    """Use the real completion timestamp, with a legacy history fallback."""
    return item.completed_at or item.created_at


def history_date(item) -> date:
    """Preserve the calendar date encoded when the task was completed."""
    return parse_timestamp(history_timestamp(item)).date()


def timestamp_as_utc(value: str) -> Optional[datetime]:
    try:
        return parse_timestamp(value).astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None
