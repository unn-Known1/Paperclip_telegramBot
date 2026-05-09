"""Basic bot handlers: /start, /help, /health, /company."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from i18n import get_strings
from middleware.auth import restricted
from middleware.audit import audited
from middleware.metrics import tracked
from middleware.rate_limit import rate_limited
from paperclip_client import get_client
from utils.chunking import send_chunked
from utils.formatting import format_company, format_health


@restricted
@rate_limited
@audited
@tracked("start")
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message with quick-action buttons."""
    s = get_strings()
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📋 Issues", callback_data="cmd:issues"),
                InlineKeyboardButton("📁 Projects", callback_data="cmd:projects"),
            ],
            [
                InlineKeyboardButton("🤖 Agents", callback_data="cmd:agents"),
                InlineKeyboardButton("❤️ Health", callback_data="cmd:health"),
            ],
            [
                InlineKeyboardButton("➕ New Issue", callback_data="cmd:create_issue"),
                InlineKeyboardButton("📖 Help", callback_data="cmd:help"),
            ],
        ]
    )
    await update.message.reply_text(s.welcome, parse_mode="HTML", reply_markup=keyboard)


@restricted
@rate_limited
@audited
@tracked("help")
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show all available commands."""
    s = get_strings()
    await send_chunked(update, s.help_text)


@restricted
@rate_limited
@audited
@tracked("health")
async def health(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check the Paperclip API health."""
    client = get_client()
    data = await client.health()
    await send_chunked(update, format_health(data))


@restricted
@rate_limited
@audited
@tracked("company")
async def company(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show current company details."""
    client = get_client()
    data = await client.get_company()
    await send_chunked(update, format_company(data))
