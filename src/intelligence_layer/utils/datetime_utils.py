"""
utils/datetime_utils.py
========================
Date and time helpers used across collectors and normalizers.

All timestamps within this module are standardized to UTC ISO-8601 format.
"""
from datetime import UTC, datetime


def utcnow() -> datetime:
    """Return the current UTC datetime (timezone-aware)."""
    return datetime.now(tz=UTC)


def to_utc_iso(dt: datetime) -> str:
    """
    Convert a datetime object to a UTC ISO-8601 string.

    Args:
        dt: A timezone-aware datetime object.

    Returns:
        ISO-8601 formatted string in UTC, e.g. "2025-07-05T12:00:00+00:00".
    """
    return dt.astimezone(UTC).isoformat()


def parse_iso(date_string: str) -> datetime:
    """
    Parse an ISO-8601 date string into a timezone-aware datetime.

    Args:
        date_string: A date string in ISO-8601 format.

    Returns:
        A timezone-aware datetime object in UTC.

    Raises:
        ValueError: If the string cannot be parsed.
    """
    dt = datetime.fromisoformat(date_string)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)
