"""Relative timestamp helpers — "2h ago" instead of raw ISO strings."""

from __future__ import annotations

import datetime


def relative_time(dt_input: str | datetime.datetime | None) -> str:
    """Convert a datetime or ISO string to a human-friendly relative string."""
    if dt_input is None:
        return "—"

    if isinstance(dt_input, str):
        try:
            dt = datetime.datetime.fromisoformat(dt_input.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return dt_input  # Return raw if unparseable
    else:
        dt = dt_input

    now = datetime.datetime.now(datetime.timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)

    delta = now - dt
    seconds = int(delta.total_seconds())

    if seconds < 0:
        return "just now"
    if seconds < 60:
        return "just now"
    if seconds < 3600:
        m = seconds // 60
        return f"{m}m ago"
    if seconds < 86400:
        h = seconds // 3600
        return f"{h}h ago"
    if seconds < 604800:
        d = seconds // 86400
        return f"{d}d ago"
    if seconds < 2592000:
        w = seconds // 604800
        return f"{w}w ago"

    return dt.strftime("%b %d, %Y")


def progress_bar(step: int, total: int, width: int = 10) -> str:
    """Render a text progress bar for multi-step wizards."""
    filled = round(step / total * width)
    empty = width - filled
    bar = "━" * filled + "░" * empty
    return f"{bar}  Step {step}/{total}"
