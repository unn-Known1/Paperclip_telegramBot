"""Simple keyword-based natural-language intent parser."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class Intent:
    """Parsed intent from a natural-language message."""

    action: str  # e.g. "list_issues", "create_issue", "help"
    filters: dict[str, str] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Vocabulary
# ---------------------------------------------------------------------------

_STATUS_WORDS: dict[str, str] = {
    "open": "open",
    "opened": "open",
    "closed": "closed",
    "close": "closed",
    "done": "closed",
    "resolved": "closed",
    "in progress": "in_progress",
    "in-progress": "in_progress",
    "wip": "in_progress",
    "backlog": "backlog",
    "todo": "todo",
    "to do": "todo",
    "to-do": "todo",
}

_PRIORITY_WORDS: dict[str, str] = {
    "critical": "critical",
    "urgent": "critical",
    "p0": "critical",
    "high": "high",
    "important": "high",
    "p1": "high",
    "medium": "medium",
    "normal": "medium",
    "p2": "medium",
    "low": "low",
    "minor": "low",
    "p3": "low",
}

_ACTION_PATTERNS: list[tuple[str, str]] = [
    (r"\b(show|list|get|display|view|see|fetch)\b.*\b(issue|bug|ticket|task)s?\b", "list_issues"),
    (r"\b(create|add|new|make|open|file)\b.*\b(issue|bug|ticket|task)\b", "create_issue"),
    (r"\b(show|list|get|display|view|see)\b.*\b(project)s?\b", "list_projects"),
    (r"\b(show|list|get|display|view|see)\b.*\b(agent|bot)s?\b", "list_agents"),
    (r"\b(show|list|get|display|view|see)\b.*\b(member|team|people)s?\b", "list_members"),
    (r"\b(show|list|get|display|view|see)\b.*\b(environment|env)s?\b", "list_environments"),
    (r"\b(show|list|get|display|view|see)\b.*\b(invite)s?\b", "list_invites"),
    (r"\b(health|status|alive|ping|up)\b", "health"),
    (r"\b(help|command|usage|how)\b", "help"),
    (r"\b(company|org|organization)\b", "company"),
    (r"\b(stats|statistics|uptime|info)\b", "stats"),
]


def parse_intent(text: str) -> Intent | None:
    """Parse a natural-language message into an Intent, or return None."""
    lower = text.lower().strip()

    # Detect action
    action: str | None = None
    for pattern, intent_action in _ACTION_PATTERNS:
        if re.search(pattern, lower):
            action = intent_action
            break

    if not action:
        return None

    # Extract optional filters
    filters: dict[str, str] = {}
    for word, status in _STATUS_WORDS.items():
        if word in lower:
            filters["status"] = status
            break

    for word, priority in _PRIORITY_WORDS.items():
        if word in lower:
            filters["priority"] = priority
            break

    return Intent(action=action, filters=filters)
