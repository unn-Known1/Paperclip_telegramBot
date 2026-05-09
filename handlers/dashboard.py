"""Dashboard handler — /dashboard shows a pinnable summary with refresh."""

from __future__ import annotations

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from middleware.auth import restricted
from middleware.audit import audited
from middleware.metrics import tracked
from middleware.rate_limit import rate_limited
from paperclip_client import get_client

logger = logging.getLogger(__name__)


async def _build_dashboard_text() -> str:
    """Build the dashboard summary text."""
    client = get_client()

    # Gather stats (best-effort)
    try:
        all_issues = await client.list_issues()
    except Exception:
        all_issues = []

    try:
        all_projects = await client.list_projects()
    except Exception:
        all_projects = []

    try:
        all_agents = await client.list_agents()
    except Exception:
        all_agents = []

    try:
        health_data = await client.health()
        api_ok = True
    except Exception:
        health_data = {}
        api_ok = False

    # Count issues by status
    open_count = sum(1 for i in all_issues if (i.get("status") or "").lower() in ("open", "todo", "backlog"))
    in_progress = sum(1 for i in all_issues if (i.get("status") or "").lower() in ("in_progress", "in-progress", "inprogress"))
    closed_count = sum(1 for i in all_issues if (i.get("status") or "").lower() in ("closed", "done", "resolved"))

    # Count by priority
    critical = sum(1 for i in all_issues if (i.get("priority") or "").lower() == "critical")
    high = sum(1 for i in all_issues if (i.get("priority") or "").lower() == "high")

    api_emoji = "✅" if api_ok else "❌"

    lines = [
        "📊 <b>Dashboard</b>",
        "",
        f"🌐 API: {api_emoji} {'Online' if api_ok else 'Offline'}",
        "",
        "<b>📋 Issues</b>",
        f"   🟢 Open: <b>{open_count}</b>",
        f"   🟡 In Progress: <b>{in_progress}</b>",
        f"   🔴 Closed: <b>{closed_count}</b>",
        f"   📊 Total: <b>{len(all_issues)}</b>",
    ]

    if critical or high:
        lines.append("")
        lines.append("<b>🚨 Attention</b>")
        if critical:
            lines.append(f"   🔴 {critical} critical issue{'s' if critical != 1 else ''}")
        if high:
            lines.append(f"   🟠 {high} high priority issue{'s' if high != 1 else ''}")

    lines.extend([
        "",
        f"📁 Projects: <b>{len(all_projects)}</b>",
        f"🤖 Agents: <b>{len(all_agents)}</b>",
        "",
        "<i>Tap 🔄 to refresh</i>",
    ])

    return "\n".join(lines)


@restricted
@rate_limited
@audited
@tracked("dashboard")
async def dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show a summary dashboard with a refresh button."""
    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)

    text = await _build_dashboard_text()
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🔄 Refresh", callback_data="dashboard:refresh"),
                InlineKeyboardButton("📌 Pin this", callback_data="dashboard:pin"),
            ]
        ]
    )
    if update.effective_message:
        await update.effective_message.reply_text(text, parse_mode="HTML", reply_markup=keyboard)


async def dashboard_refresh_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Refresh the dashboard message in-place."""
    query = update.callback_query
    await query.answer("Refreshing...")
    text = await _build_dashboard_text()
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🔄 Refresh", callback_data="dashboard:refresh"),
                InlineKeyboardButton("📌 Pin this", callback_data="dashboard:pin"),
            ]
        ]
    )
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=keyboard)


async def dashboard_pin_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Pin the dashboard message."""
    query = update.callback_query
    try:
        await query.message.pin(disable_notification=True)
        await query.answer("📌 Pinned!")
    except Exception:
        await query.answer("❌ Can't pin — I may need admin rights.", show_alert=True)
