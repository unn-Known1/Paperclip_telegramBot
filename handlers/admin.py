"""Admin handlers: /stats, /broadcast."""

from __future__ import annotations

import os
import pathlib
import time

from telegram import Update
from telegram.ext import ContextTypes

import config
from i18n import get_strings
from middleware.auth import admin_only, restricted
from middleware.audit import audited, recent_activities
from middleware.metrics import tracked
from middleware.rate_limit import rate_limited
from paperclip_client import get_client
from utils.chunking import send_chunked
from utils.timestamps import relative_time

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
    if update.effective_message:
        await update.effective_message.reply_text(text, parse_mode="HTML")


@restricted
@admin_only
@audited
@tracked("broadcast")
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Broadcast a message to all allowed users."""
    s = get_strings()
    args = context.args
    if not args:
        if update.effective_message:
            await update.effective_message.reply_text(s.broadcast_prompt)
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

    if update.effective_message:
        await update.effective_message.reply_text(s.broadcast_sent.format(count=sent))


@restricted
@admin_only
@rate_limited
@audited
@tracked("activities")
async def activities(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the most recent bot activities (admin only)."""
    if not recent_activities:
        if update.effective_message:
            await update.effective_message.reply_text("📭 No recent activity logs found.")
        return

    lines = ["📊 <b>Live Activity Logs</b>\n"]
    
    # Iterate in reverse to show the most recent first
    for idx, act in enumerate(reversed(recent_activities)):
        status_emoji = "✅" if act.get("status") == "success" else "❌"
        cmd = act.get("command", "unknown")
        user = act.get("username") or act.get("user_id") or "Unknown"
        ms = act.get("response_time_ms", 0)
        # Parse ISO timestamp for relative time
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(act.get("timestamp"))
            rel_time = relative_time(dt.isoformat() + "Z") # Add Z so it parses as UTC-ish or just pass it
            
            # Formatting timestamp nicer:
            ts = dt.strftime("%H:%M:%S")
        except Exception:
            ts = "Unknown time"
            
        lines.append(f"{status_emoji} <b>{user}</b> ran <code>{cmd}</code>")
        
        detail_str = f"   ⏱ {ms}ms  │  🕐 {ts}"
        if act.get("error"):
            # Add error info if failed
            detail_str += f"\n   ⚠️ <i>{act.get('error')}</i>"
            
        lines.append(detail_str)
        lines.append("") # Empty line between logs

    text = "\n".join(lines)
    await send_chunked(update, text, parse_mode="HTML")


@restricted
@admin_only
@rate_limited
@audited
@tracked("explore")
async def explore_folder(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Explore the bot's local project directory (admin only)."""
    args = context.args or []
    
    # Base directory is the current working directory where the bot runs
    base_path = pathlib.Path(os.getcwd()).resolve()
    
    # If a path argument is provided, append it to base_path
    target_path = base_path
    if args:
        requested_path = " ".join(args)
        # Prevent absolute paths or relative paths traversing outside the base directory
        target_path = (base_path / requested_path).resolve()
        if not str(target_path).startswith(str(base_path)):
            if update.effective_message:
                await update.effective_message.reply_text("❌ Access denied: Path must be within the project folder.")
            return

    if not target_path.exists():
        if update.effective_message:
            await update.effective_message.reply_text(f"❌ Path not found: {target_path.relative_to(base_path)}")
        return

    if target_path.is_file():
        # It's a file, show its size and maybe some basic info
        file_size = target_path.stat().st_size
        text = f"📄 <b>File:</b> <code>{target_path.relative_to(base_path)}</code>\n"
        text += f"📏 <b>Size:</b> {file_size} bytes"
        if update.effective_message:
            await update.effective_message.reply_text(text, parse_mode="HTML")
        return

    # It's a directory, list its contents
    try:
        items = list(target_path.iterdir())
    except PermissionError:
        if update.effective_message:
            await update.effective_message.reply_text("❌ Permission denied reading this folder.")
        return

    # Sort directories first, then files
    items.sort(key=lambda x: (not x.is_dir(), x.name.lower()))

    lines = [f"📂 <b>Contents of</b> <code>{target_path.relative_to(base_path) if target_path != base_path else '/'}</code>", ""]
    
    if not items:
        lines.append("<i>Empty directory</i>")
    else:
        for item in items:
            if item.is_dir():
                lines.append(f"📁 <code>{item.name}/</code>")
            else:
                size_kb = item.stat().st_size / 1024
                lines.append(f"📄 <code>{item.name}</code> <i>({size_kb:.1f} KB)</i>")

    text = "\n".join(lines)
    await send_chunked(update, text, parse_mode="HTML")
