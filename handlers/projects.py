"""Project handler: /projects with pagination."""

from telegram import Update
from telegram.ext import ContextTypes

from i18n import get_strings
from middleware.auth import restricted
from middleware.audit import audited
from middleware.metrics import tracked
from middleware.rate_limit import rate_limited
from paperclip_client import get_client
from utils.formatting import format_project
from utils.pagination import paginate
from utils.chunking import send_chunked


@restricted
@rate_limited
@audited
@tracked("projects")
async def projects(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all projects with pagination."""
    client = get_client()
    s = get_strings()
    items = await client.list_projects()

    if not items:
        await update.message.reply_text(s.no_projects)
        return

    context.user_data["projects_cache"] = items
    text, keyboard = paginate(items, page=0, prefix="projects", formatter=format_project)
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=keyboard)


async def projects_pagination_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle page navigation for projects."""
    query = update.callback_query
    await query.answer()
    page = int(query.data.split(":")[-1])
    items = context.user_data.get("projects_cache", [])
    if not items:
        await query.edit_message_text("Session expired. Use /projects again.")
        return
    text, keyboard = paginate(items, page=page, prefix="projects", formatter=format_project)
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=keyboard)
