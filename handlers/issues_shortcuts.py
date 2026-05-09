"""Status shortcut handlers: /close, /reopen, /close_all, and undo."""

import asyncio
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from i18n import get_strings
from middleware.auth import restricted
from middleware.audit import audited
from middleware.metrics import tracked
from middleware.rate_limit import rate_limited
from paperclip_client import get_client
from utils.formatting import format_issue_detail

logger = logging.getLogger(__name__)


@restricted
@rate_limited
@audited
@tracked("close_issue")
async def close_issue(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shortcut to close an issue."""
    s = get_strings()
    args = context.args or []
    if not args:
        await update.message.reply_text(s.close_usage, parse_mode="HTML")
        return

    issue_id = args[0]
    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    client = get_client()
    try:
        # Fetch current state for undo
        current = await client.get_issue(issue_id)
        result = await client.update_issue(issue_id, status="closed")

        # Save for undo
        undo_key = f"undo_status_{issue_id}"
        context.user_data[undo_key] = current.get("status", "open")

        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton(s.undo_prompt, callback_data=f"undo:status:{issue_id}")]]
        )

        msg = await update.message.reply_text(
            s.close_success.format(details=format_issue_detail(result)),
            parse_mode="HTML",
            reply_markup=keyboard,
        )

        # Remove undo button after 30s
        async def remove_undo(ctx: ContextTypes.DEFAULT_TYPE):
            try:
                await ctx.bot.edit_message_reply_markup(
                    chat_id=msg.chat_id, message_id=msg.message_id, reply_markup=None
                )
            except Exception:
                pass

        if context.job_queue:
            context.job_queue.run_once(remove_undo, 30, chat_id=msg.chat_id)

    except Exception:
        await update.message.reply_text(s.update_issue_not_found)


@restricted
@rate_limited
@audited
@tracked("reopen_issue")
async def reopen_issue(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shortcut to reopen an issue."""
    s = get_strings()
    args = context.args or []
    if not args:
        await update.message.reply_text(s.reopen_usage, parse_mode="HTML")
        return

    issue_id = args[0]
    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    client = get_client()
    try:
        current = await client.get_issue(issue_id)
        result = await client.update_issue(issue_id, status="open")

        undo_key = f"undo_status_{issue_id}"
        context.user_data[undo_key] = current.get("status", "closed")

        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton(s.undo_prompt, callback_data=f"undo:status:{issue_id}")]]
        )

        msg = await update.message.reply_text(
            s.reopen_success.format(details=format_issue_detail(result)),
            parse_mode="HTML",
            reply_markup=keyboard,
        )

        async def remove_undo(ctx: ContextTypes.DEFAULT_TYPE):
            try:
                await ctx.bot.edit_message_reply_markup(
                    chat_id=msg.chat_id, message_id=msg.message_id, reply_markup=None
                )
            except Exception:
                pass

        if context.job_queue:
            context.job_queue.run_once(remove_undo, 30, chat_id=msg.chat_id)

    except Exception:
        await update.message.reply_text(s.update_issue_not_found)


@restricted
@rate_limited
@audited
@tracked("close_all")
async def close_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Bulk close all open issues."""
    s = get_strings()
    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    client = get_client()
    try:
        open_issues = await client.list_issues(status="open")
        if not open_issues:
            await update.message.reply_text(s.bulk_close_usage)
            return

        context.user_data["bulk_close_ids"] = [i["id"] for i in open_issues]

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(f"✅ {s.confirm}", callback_data="bulk_close:confirm"),
                    InlineKeyboardButton(f"❌ {s.cancel}", callback_data="bulk_close:cancel"),
                ]
            ]
        )
        await update.message.reply_text(
            s.bulk_close_confirm.format(count=len(open_issues)),
            parse_mode="HTML",
            reply_markup=keyboard,
        )
    except Exception as e:
        logger.error("Error fetching open issues: %s", e)
        await update.message.reply_text(s.error_generic)


async def bulk_close_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle bulk close confirmation."""
    query = update.callback_query
    await query.answer()
    s = get_strings()

    if query.data == "bulk_close:cancel":
        context.user_data.pop("bulk_close_ids", None)
        await query.edit_message_text(s.bulk_close_cancelled)
        return

    ids = context.user_data.pop("bulk_close_ids", [])
    if not ids:
        await query.edit_message_text(s.bulk_close_usage)
        return

    await query.edit_message_text("Closing issues...")
    client = get_client()
    count = 0
    for issue_id in ids:
        try:
            await client.update_issue(issue_id, status="closed")
            count += 1
            await asyncio.sleep(0.1)  # gentle rate limiting
        except Exception:
            pass

    await query.edit_message_text(s.bulk_close_success.format(count=count))


async def undo_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle undo requests."""
    query = update.callback_query
    s = get_strings()

    parts = query.data.split(":")
    action = parts[1]
    issue_id = parts[2]

    if action == "status":
        undo_key = f"undo_status_{issue_id}"
        prev_status = context.user_data.pop(undo_key, None)

        if not prev_status:
            await query.answer(s.undo_expired, show_alert=True)
            try:
                await query.message.edit_reply_markup(reply_markup=None)
            except Exception:
                pass
            return

        client = get_client()
        try:
            await client.update_issue(issue_id, status=prev_status)
            await query.answer("Undone!")
            await query.edit_message_text(
                s.undo_success.format(id=issue_id), parse_mode="HTML"
            )
        except Exception:
            await query.answer("Failed to undo.", show_alert=True)
