"""Agent handler: /agents with pagination."""

from telegram import Update
from telegram.ext import ContextTypes

from i18n import get_strings
from middleware.auth import restricted
from middleware.audit import audited
from middleware.metrics import tracked
from middleware.rate_limit import rate_limited
from paperclip_client import get_client
from utils.formatting import format_agent
from utils.pagination import paginate


@restricted
@rate_limited
@audited
@tracked("agents")
async def agents(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all agents with pagination."""
    client = get_client()
    s = get_strings()
    items = await client.list_agents()

    if not items:
        await update.message.reply_text(s.no_agents)
        return

    context.user_data["agents_cache"] = items
    text, keyboard = paginate(items, page=0, prefix="agents", formatter=format_agent)
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=keyboard)


async def agents_pagination_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle page navigation for agents."""
    query = update.callback_query
    await query.answer()
    page = int(query.data.split(":")[-1])
    items = context.user_data.get("agents_cache", [])
    if not items:
        await query.edit_message_text("Session expired. Use /agents again.")
        return
    text, keyboard = paginate(items, page=page, prefix="agents", formatter=format_agent)
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=keyboard)
