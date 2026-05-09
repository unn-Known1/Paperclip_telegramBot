"""Admin handlers: /stats, /broadcast."""

from __future__ import annotations

import time

from telegram import Update
from telegram.ext import ContextTypes

import config
from i18n import get_strings
from middleware.auth import admin_only, restricted
from middleware.audit import audited
from middleware.metrics import tracked
from middleware.rate_limit import rate_limited
from paperclip_client import get_client

# Track bot start time for uptime calculation
_start_time: float = time.monotonic()
_commands_processed: int = 0


def increment_command_count() -> None:
    """Call from the main middleware to count commands."""
    global _commands_processed
    _commands_processed += 1


@restricted
@admin_only
@rate_limited
@audited
@tracked("stats")
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show bot statistics (admin only)."""
    uptime_seconds = int(time.monotonic() - _start_time)
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    # Quick API health check
    client = get_client()
    try:
        await client.health()
        api_status = "✅ Online"
    except Exception:
        api_status = "❌ Offline"

    text = (
        "📊 <b>Bot Statistics</b>\n\n"
        f"⏱ Uptime: <b>{hours}h {minutes}m {seconds}s</b>\n"
        f"📨 Commands processed: <b>{_commands_processed}</b>\n"
        f"👥 Allowed users: <b>{len(config.ALLOWED_USER_IDS)}</b>\n"
        f"🔧 Admin users: <b>{len(config.ADMIN_USER_IDS)}</b>\n"
        f"🌐 API: {api_status}\n"
        f"📡 Mode: <b>{'Webhook' if config.WEBHOOK_URL else 'Polling'}</b>"
    )
    await update.message.reply_text(text, parse_mode="HTML")


@restricted
@admin_only
@audited
@tracked("broadcast")
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Broadcast a message to all allowed users."""
    s = get_strings()
    args = context.args
    if not args:
        await update.message.reply_text(s.broadcast_prompt)
        return

    message = " ".join(args)
    sent = 0
    for user_id in config.ALLOWED_USER_IDS:
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"📢 <b>Broadcast</b>\n\n{message}",
                parse_mode="HTML",
            )
            sent += 1
        except Exception:
            pass

    await update.message.reply_text(s.broadcast_sent.format(count=sent))
