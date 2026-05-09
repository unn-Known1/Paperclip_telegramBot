"""Handler registration — wires all commands and callbacks to the Application."""

from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    InlineQueryHandler,
    MessageHandler,
    filters,
)

from handlers.basic import company, health, help_command, start, notify, notify_callback, onboarding_callback, _issue_action_keyboard
from handlers.issues import (
    get_create_issue_handler,
    get_update_issue_handler,
    issues,
    issues_filter_callback,
    issues_pagination_callback,
)
from handlers.projects import projects, projects_pagination_callback
from handlers.agents import agents, agents_pagination_callback
from handlers.resources import environments, envs_pagination_callback, invites, members
from handlers.admin import broadcast, stats
from handlers.digest import schedule_digest
from handlers.inline import inline_query
from handlers.dashboard import dashboard, dashboard_refresh_callback, dashboard_pin_callback
from handlers.search import search_issues
from handlers.issues_shortcuts import close_issue, reopen_issue, close_all, bulk_close_callback, undo_callback

from middleware.auth import restricted
from middleware.rate_limit import rate_limited
from middleware.audit import audited
from middleware.metrics import tracked
from utils.nlp import parse_intent
from utils.chunking import send_chunked
from i18n import get_strings
from paperclip_client import get_client
from utils.formatting import format_issue


# ---------------------------------------------------------------------------
# Natural-language fallback handler
# ---------------------------------------------------------------------------

@restricted
@rate_limited
@audited
@tracked("nlp")
async def handle_message(update, context):
    """Try NLP parsing on non-command text messages."""
    text = update.message.text or ""

    # Check for reply keyboard triggers first
    reply_map = {
        "📋 Issues": lambda u, c: issues(u, c),
        "➕ New Issue": _nlp_create_hint,
        "📁 Projects": lambda u, c: projects(u, c),
        "📊 Dashboard": lambda u, c: dashboard(u, c),
        "❤️ Health": lambda u, c: health(u, c),
        "📖 Help": lambda u, c: help_command(u, c),
    }
    
    if text in reply_map:
        context.args = []
        await reply_map[text](update, context)
        return

    intent = parse_intent(text)
    if not intent:
        s = get_strings()
        await update.message.reply_text(s.nlp_no_match, parse_mode="HTML")
        return

    # Dispatch based on parsed intent
    action_map = {
        "list_issues": _nlp_list_issues,
        "list_projects": lambda u, c, f: projects(u, c),
        "list_agents": lambda u, c, f: agents(u, c),
        "list_members": lambda u, c, f: members(u, c),
        "list_environments": lambda u, c, f: environments(u, c),
        "list_invites": lambda u, c, f: invites(u, c),
        "health": lambda u, c, f: health(u, c),
        "help": lambda u, c, f: help_command(u, c),
        "company": lambda u, c, f: company(u, c),
        "stats": lambda u, c, f: stats(u, c),
        "create_issue": _nlp_create_hint,
    }

    handler = action_map.get(intent.action)
    if handler:
        await handler(update, context, intent.filters)
    else:
        s = get_strings()
        await update.message.reply_text(s.nlp_no_match, parse_mode="HTML")


async def _nlp_list_issues(update, context, nlp_filters):
    """Handle NLP-detected issue listing with extracted filters."""
    from utils.pagination import paginate
    client = get_client()
    s = get_strings()
    items = await client.list_issues(
        status=nlp_filters.get("status"),
        priority=nlp_filters.get("priority"),
    )
    if not items:
        await update.message.reply_text(s.no_issues)
        return
    context.user_data["issues_cache"] = items
    text, keyboard = paginate(items, page=0, prefix="issues", formatter=format_issue)
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=keyboard)


async def _nlp_create_hint(update, context, _filters=None):
    """Hint the user to use /create_issue."""
    await update.message.reply_text(
        "💡 Use /create_issue to start the issue creation wizard.",
        parse_mode="HTML",
    )


# ---------------------------------------------------------------------------
# Quick-action callback handler
# ---------------------------------------------------------------------------

async def quick_action_callback(update, context):
    """Handle inline button quick actions from the /start menu."""
    query = update.callback_query
    await query.answer()
    cmd = query.data.split(":")[-1]

    dispatch = {
        "issues": issues,
        "projects": projects,
        "agents": agents,
        "health": health,
        "help": help_command,
        "dashboard": dashboard,
        "create_issue": None,
    }

    handler = dispatch.get(cmd)
    if handler:
        await query.message.reply_text("⏳ Loading...")
        context.args = []
        try:
            await handler(update, context)
        except Exception:
            pass
    elif cmd == "create_issue":
        await query.message.reply_text(
            "💡 Use /create_issue to start the issue creation wizard."
        )


async def issue_action_callback(update, context):
    """Handle per-issue inline buttons (Edit, Status, Close, Pin)."""
    query = update.callback_query
    await query.answer()
    parts = query.data.split(":")
    action = parts[1]
    issue_id = parts[2]
    
    if action == "edit":
        await query.message.reply_text(f"💡 Use /update_issue {issue_id} to edit.")
    elif action == "status":
        await query.message.reply_text(f"💡 Use /update_issue {issue_id} to change status.")
    elif action == "close":
        context.args = [issue_id]
        await close_issue(update, context)
    elif action == "pin":
        try:
            await query.message.pin(disable_notification=True)
            await query.answer("📌 Pinned!")
        except Exception:
            await query.answer("❌ Can't pin — missing admin rights.", show_alert=True)


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def register_handlers(application: Application) -> None:
    """Register all handlers on the application."""

    # Inline query mode
    application.add_handler(InlineQueryHandler(inline_query))

    # Basic commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("health", health))
    application.add_handler(CommandHandler("company", company))
    application.add_handler(CommandHandler("dashboard", dashboard))
    application.add_handler(CommandHandler("notify", notify))

    # Issue commands
    application.add_handler(get_create_issue_handler())
    application.add_handler(get_update_issue_handler())
    application.add_handler(CommandHandler("issues", issues))
    application.add_handler(CommandHandler("search", search_issues))
    application.add_handler(CommandHandler("close", close_issue))
    application.add_handler(CommandHandler("reopen", reopen_issue))
    application.add_handler(CommandHandler("close_all", close_all))

    # Resource commands
    application.add_handler(CommandHandler("projects", projects))
    application.add_handler(CommandHandler("agents", agents))
    application.add_handler(CommandHandler("environments", environments))
    application.add_handler(CommandHandler("members", members))
    application.add_handler(CommandHandler("invites", invites))

    # Admin commands
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("broadcast", broadcast))

    # Callback queries
    application.add_handler(CallbackQueryHandler(issues_pagination_callback, pattern=r"^issues:page:"))
    application.add_handler(CallbackQueryHandler(issues_filter_callback, pattern=r"^issues:filter:"))
    application.add_handler(CallbackQueryHandler(projects_pagination_callback, pattern=r"^projects:page:"))
    application.add_handler(CallbackQueryHandler(agents_pagination_callback, pattern=r"^agents:page:"))
    application.add_handler(CallbackQueryHandler(envs_pagination_callback, pattern=r"^envs:page:"))
    
    # Feature callbacks
    application.add_handler(CallbackQueryHandler(dashboard_refresh_callback, pattern=r"^dashboard:refresh$"))
    application.add_handler(CallbackQueryHandler(dashboard_pin_callback, pattern=r"^dashboard:pin$"))
    application.add_handler(CallbackQueryHandler(onboarding_callback, pattern=r"^onboard:"))
    application.add_handler(CallbackQueryHandler(notify_callback, pattern=r"^notify:"))
    application.add_handler(CallbackQueryHandler(bulk_close_callback, pattern=r"^bulk_close:"))
    application.add_handler(CallbackQueryHandler(undo_callback, pattern=r"^undo:"))
    application.add_handler(CallbackQueryHandler(issue_action_callback, pattern=r"^iact:"))

    # Quick-action buttons from /start
    application.add_handler(CallbackQueryHandler(quick_action_callback, pattern=r"^cmd:"))

    # Ignore no-op buttons
    application.add_handler(CallbackQueryHandler(lambda u, c: u.callback_query.answer(), pattern=r"^noop$"))

    # Natural-language fallback
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Scheduled digest
    schedule_digest(application)
