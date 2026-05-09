"""Basic handlers: /start (with deep linking + onboarding), /help, /health,
/company, /notify, and the persistent reply keyboard."""

from __future__ import annotations

from telegram import (
    ChatAction,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    Update,
)
from telegram.ext import ContextTypes

from i18n import get_strings
from middleware.auth import restricted
from middleware.audit import audited
from middleware.metrics import tracked
from middleware.rate_limit import rate_limited
from paperclip_client import get_client
from utils.chunking import send_chunked
from utils.formatting import format_company, format_health, format_issue_detail


# ---------------------------------------------------------------------------
# Persistent reply keyboard (always visible at the bottom of the chat)
# ---------------------------------------------------------------------------

REPLY_KEYBOARD = ReplyKeyboardMarkup(
    [
        [KeyboardButton("📋 Issues"), KeyboardButton("➕ New Issue")],
        [KeyboardButton("📁 Projects"), KeyboardButton("📊 Dashboard")],
        [KeyboardButton("❤️ Health"), KeyboardButton("📖 Help")],
    ],
    resize_keyboard=True,
    is_persistent=True,
)


# ---------------------------------------------------------------------------
# /start — with deep linking + first-time onboarding
# ---------------------------------------------------------------------------

@restricted
@rate_limited
@audited
@tracked("start")
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start, including deep links like /start issue_<id>."""
    s = get_strings()

    # --- Deep linking ---
    args = context.args or []
    if args:
        payload = args[0]
        # Handle issue deep links: t.me/bot?start=issue_<id>
        if payload.startswith("issue_"):
            issue_id = payload[6:]
            await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
            client = get_client()
            try:
                issue = await client.get_issue(issue_id)
                text = format_issue_detail(issue)
                keyboard = _issue_action_keyboard(issue_id)
                await update.message.reply_text(
                    text, parse_mode="HTML",
                    reply_markup=keyboard,
                )
            except Exception:
                await update.message.reply_text(s.update_issue_not_found)
            return

    # --- First-time onboarding ---
    if not context.user_data.get("onboarded"):
        await _onboarding_step1(update, context)
        return

    # --- Normal /start ---
    inline_keyboard = InlineKeyboardMarkup(
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
                InlineKeyboardButton("📊 Dashboard", callback_data="cmd:dashboard"),
            ],
        ]
    )
    await update.message.reply_text(
        s.welcome, parse_mode="HTML",
        reply_markup=REPLY_KEYBOARD,
    )
    await update.message.reply_text(
        "Quick actions:", reply_markup=inline_keyboard,
    )


# ---------------------------------------------------------------------------
# Onboarding steps
# ---------------------------------------------------------------------------

async def _onboarding_step1(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    s = get_strings()
    keyboard = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("Next ▶", callback_data="onboard:2"),
            InlineKeyboardButton("Skip ⏭", callback_data="onboard:done"),
        ]]
    )
    await update.message.reply_text(s.onboarding_step1, parse_mode="HTML", reply_markup=keyboard)


async def onboarding_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle onboarding step navigation."""
    query = update.callback_query
    await query.answer()
    s = get_strings()
    step = query.data.split(":")[-1]

    if step == "2":
        keyboard = InlineKeyboardMarkup(
            [[
                InlineKeyboardButton("◀ Back", callback_data="onboard:1"),
                InlineKeyboardButton("Next ▶", callback_data="onboard:3"),
            ]]
        )
        await query.edit_message_text(s.onboarding_step2, parse_mode="HTML", reply_markup=keyboard)
    elif step == "3":
        keyboard = InlineKeyboardMarkup(
            [[
                InlineKeyboardButton("◀ Back", callback_data="onboard:2"),
                InlineKeyboardButton("Done ✅", callback_data="onboard:done"),
            ]]
        )
        await query.edit_message_text(s.onboarding_step3, parse_mode="HTML", reply_markup=keyboard)
    elif step == "1":
        keyboard = InlineKeyboardMarkup(
            [[
                InlineKeyboardButton("Next ▶", callback_data="onboard:2"),
                InlineKeyboardButton("Skip ⏭", callback_data="onboard:done"),
            ]]
        )
        await query.edit_message_text(s.onboarding_step1, parse_mode="HTML", reply_markup=keyboard)
    elif step == "done":
        context.user_data["onboarded"] = True
        await query.edit_message_text(s.onboarding_complete, parse_mode="HTML")
        # Send the persistent reply keyboard
        await query.message.reply_text(
            "Use the buttons below anytime! 👇", reply_markup=REPLY_KEYBOARD,
        )


# ---------------------------------------------------------------------------
# /help
# ---------------------------------------------------------------------------

@restricted
@rate_limited
@audited
@tracked("help")
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show all available commands."""
    s = get_strings()
    await send_chunked(update, s.help_text)


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------

@restricted
@rate_limited
@audited
@tracked("health")
async def health(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check the Paperclip API health."""
    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    client = get_client()
    data = await client.health()
    await send_chunked(update, format_health(data))


# ---------------------------------------------------------------------------
# /company
# ---------------------------------------------------------------------------

@restricted
@rate_limited
@audited
@tracked("company")
async def company(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show current company details."""
    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    client = get_client()
    data = await client.get_company()
    await send_chunked(update, format_company(data))


# ---------------------------------------------------------------------------
# /notify — notification preferences
# ---------------------------------------------------------------------------

@restricted
@rate_limited
@audited
@tracked("notify")
async def notify(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show/set notification preferences."""
    s = get_strings()
    prefs = context.user_data.get("notify_prefs", {"digest": True, "assignments": True})
    context.user_data["notify_prefs"] = prefs

    digest_icon = "✅" if prefs.get("digest") else "❌"
    assign_icon = "✅" if prefs.get("assignments") else "❌"
    status = f"Digest: {digest_icon} | Assignments: {assign_icon}"

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    f"{'🔔' if prefs.get('digest') else '🔕'} Daily Digest",
                    callback_data="notify:toggle:digest",
                ),
                InlineKeyboardButton(
                    f"{'🔔' if prefs.get('assignments') else '🔕'} Assignments",
                    callback_data="notify:toggle:assignments",
                ),
            ],
            [
                InlineKeyboardButton("🔕 All Off", callback_data="notify:all_off"),
                InlineKeyboardButton("🔔 All On", callback_data="notify:all_on"),
            ],
        ]
    )
    await update.message.reply_text(
        s.notify_usage.format(status=status), parse_mode="HTML", reply_markup=keyboard,
    )


async def notify_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle notification preference toggles."""
    query = update.callback_query
    await query.answer()
    s = get_strings()

    prefs = context.user_data.get("notify_prefs", {"digest": True, "assignments": True})
    action = query.data  # e.g. "notify:toggle:digest"

    if action == "notify:all_off":
        prefs = {"digest": False, "assignments": False}
        setting = "All notifications off"
    elif action == "notify:all_on":
        prefs = {"digest": True, "assignments": True}
        setting = "All notifications on"
    elif action.startswith("notify:toggle:"):
        key = action.split(":")[-1]
        prefs[key] = not prefs.get(key, True)
        setting = f"{key.capitalize()}: {'on' if prefs[key] else 'off'}"
    else:
        return

    context.user_data["notify_prefs"] = prefs
    await query.edit_message_text(
        s.notify_updated.format(setting=setting), parse_mode="HTML",
    )


# ---------------------------------------------------------------------------
# Shared helper: per-issue action keyboard
# ---------------------------------------------------------------------------

def _issue_action_keyboard(issue_id: str) -> InlineKeyboardMarkup:
    """Build contextual action buttons for a specific issue."""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✏️ Edit", callback_data=f"iact:edit:{issue_id}"),
                InlineKeyboardButton("🔄 Status", callback_data=f"iact:status:{issue_id}"),
            ],
            [
                InlineKeyboardButton("🔴 Close", callback_data=f"iact:close:{issue_id}"),
                InlineKeyboardButton("📌 Pin", callback_data=f"iact:pin:{issue_id}"),
            ],
        ]
    )
