"""Rich HTML formatting for Telegram messages."""

from html import escape
from typing import Any

# ---------------------------------------------------------------------------
# Emoji maps
# ---------------------------------------------------------------------------
STATUS_EMOJI: dict[str, str] = {
    "open": "🟢",
    "in_progress": "🟡",
    "in-progress": "🟡",
    "inprogress": "🟡",
    "closed": "🔴",
    "done": "🔴",
    "resolved": "🔴",
    "backlog": "⚪",
    "todo": "🔵",
}

PRIORITY_EMOJI: dict[str, str] = {
    "critical": "🔴",
    "high": "🟠",
    "medium": "🟡",
    "low": "🟢",
    "none": "⚪",
}


def _e(text: Any) -> str:
    """HTML-escape a value."""
    return escape(str(text)) if text else "—"


# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------

def format_issue(issue: dict) -> str:
    """Format a single issue for list views."""
    title = _e(issue.get("title", "Untitled"))
    status = (issue.get("status") or "unknown").lower()
    priority = (issue.get("priority") or "none").lower()
    issue_id = _e(issue.get("id"))

    s_emoji = STATUS_EMOJI.get(status, "❓")
    p_emoji = PRIORITY_EMOJI.get(priority, "⚪")

    return (
        f"{s_emoji} <b>{title}</b>\n"
        f"   {p_emoji} {_e(priority.capitalize())} │ {_e(status.capitalize())}\n"
        f"   🆔 <code>{issue_id}</code>"
    )


def format_issue_detail(issue: dict) -> str:
    """Format a full issue detail view."""
    title = _e(issue.get("title", "Untitled"))
    status = (issue.get("status") or "unknown").lower()
    priority = (issue.get("priority") or "none").lower()
    desc = _e(issue.get("description")) or "<i>No description</i>"
    issue_id = _e(issue.get("id"))

    s_emoji = STATUS_EMOJI.get(status, "❓")
    p_emoji = PRIORITY_EMOJI.get(priority, "⚪")

    lines = [
        f"📋 <b>{title}</b>",
        "",
        f"{s_emoji} Status: {_e(status.capitalize())}",
        f"{p_emoji} Priority: {_e(priority.capitalize())}",
        f"🆔 ID: <code>{issue_id}</code>",
        "",
        f"📝 {desc}",
    ]

    if issue.get("assigneeAgentId"):
        lines.append(f"👤 Assigned: <code>{_e(issue['assigneeAgentId'])}</code>")
    if issue.get("projectId"):
        lines.append(f"📁 Project: <code>{_e(issue['projectId'])}</code>")

    return "\n".join(lines)


def format_project(project: dict) -> str:
    """Format a single project."""
    name = _e(project.get("name", "Unnamed"))
    pid = _e(project.get("id"))
    return f"📁 <b>{name}</b>\n   🆔 <code>{pid}</code>"


def format_agent(agent: dict) -> str:
    """Format a single agent."""
    name = _e(agent.get("name", "Unknown"))
    role = _e(agent.get("role"))
    aid = _e(agent.get("id"))
    return f"🤖 <b>{name}</b> — {role}\n   🆔 <code>{aid}</code>"


def format_member(member: dict) -> str:
    """Format a single member."""
    name = _e(member.get("name", member.get("email", "Unknown")))
    role = _e(member.get("role"))
    return f"👤 <b>{name}</b> — {role}"


def format_environment(env: dict) -> str:
    """Format a single environment."""
    name = _e(env.get("name", "Unknown"))
    eid = _e(env.get("id"))
    return f"🌍 <b>{name}</b>\n   🆔 <code>{eid}</code>"


def format_invite(invite: dict) -> str:
    """Format a single invite."""
    email = _e(invite.get("email", "Unknown"))
    status = _e(invite.get("status"))
    return f"✉️ <b>{email}</b> — {status}"


def format_company(company: dict) -> str:
    """Format company details."""
    name = _e(company.get("name", "Unknown"))
    cid = _e(company.get("id"))
    lines = [
        "🏢 <b>Company Details</b>",
        "",
        f"   Name: <b>{name}</b>",
        f"   🆔 <code>{cid}</code>",
    ]
    return "\n".join(lines)


def format_health(data: dict) -> str:
    """Format API health response."""
    status = (data.get("status") or "unknown").lower()
    emoji = "✅" if status in ("ok", "healthy", "up") else "❌"
    lines = [f"{emoji} <b>API Health</b>", ""]
    for key, value in data.items():
        lines.append(f"   {_e(key)}: <b>{_e(value)}</b>")
    return "\n".join(lines)
