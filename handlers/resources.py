"""Resource handlers: /environments, /members, /invites."""

from telegram import Update
from telegram.ext import ContextTypes

from i18n import get_strings
from middleware.auth import restricted
from middleware.audit import audited
from middleware.metrics import tracked
from middleware.rate_limit import rate_limited
from paperclip_client import get_client
from utils.chunking import send_chunked
from utils.formatting import format_environment, format_invite, format_member
from utils.pagination import paginate


@restricted
@rate_limited
@audited
@tracked("environments")
async def environments(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all environments."""
    client = get_client()
    s = get_strings()
    items = await client.list_environments()

    if not items:
        await update.message.reply_text(s.no_environments)
        return

    context.user_data["envs_cache"] = items
    text, keyboard = paginate(items, page=0, prefix="envs", formatter=format_environment)
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=keyboard)


async def envs_pagination_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle page navigation for environments."""
    query = update.callback_query
    await query.answer()
    page = int(query.data.split(":")[-1])
    items = context.user_data.get("envs_cache", [])
    if not items:
        await query.edit_message_text("Session expired. Use /environments again.")
        return
    text, keyboard = paginate(items, page=page, prefix="envs", formatter=format_environment)
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=keyboard)


@restricted
@rate_limited
@audited
@tracked("members")
async def members(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all team members."""
    client = get_client()
    s = get_strings()
    data = await client.list_members()

    # API may return a list or a dict with a key
    items = data if isinstance(data, list) else data.get("members", data.get("data", []))

    if not items:
        await update.message.reply_text(s.no_members)
        return

    text = "\n\n".join(format_member(m) for m in items)
    await send_chunked(update, f"👥 <b>Team Members</b>\n\n{text}")


@restricted
@rate_limited
@audited
@tracked("invites")
async def invites(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all pending invites."""
    client = get_client()
    s = get_strings()
    data = await client.list_invites()

    items = data if isinstance(data, list) else data.get("invites", data.get("data", []))

    if not items:
        await update.message.reply_text(s.no_invites)
        return

    text = "\n\n".join(format_invite(i) for i in items)
    await send_chunked(update, f"✉️ <b>Pending Invites</b>\n\n{text}")
