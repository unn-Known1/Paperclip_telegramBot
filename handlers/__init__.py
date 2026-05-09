"""Handler registration — wires all commands and callbacks to the Application."""

from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, filters

from handlers.basic import company, health, help_command, start
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
from middleware.auth import restricted
from middleware.rate_limit import rate_limited
from middleware.audit import audited
from middleware.metrics import tracked
from utils.nlp import parse_intent
from utils.chunking import send_chunked
from i18n import get_strings
from paperclip_client import get_client
from utils.formatting import format_issue
from utils.pagination import paginate


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


async def _nlp_create_hint(update, context, _filters):
    """Hint the user to use /create_issue."""
    await update.message.reply_text(
        "💡 Use /create_issue to start the issue creation wizard.",
        parse_mode="HTML",
    )


# ---------------------------------------------------------------------------
# Quick-action callback handler (from /start inline buttons)
# ---------------------------------------------------------------------------

async def quick_action_callback(update, context):
    """Handle inline button quick actions from the /start menu."""
    query = update.callback_query
    await query.answer()
    cmd = query.data.split(":")[-1]  # e.g. "issues", "health"

    dispatch = {
        "issues": issues,
        "projects": projects,
        "agents": agents,
        "health": health,
        "help": help_command,
        "create_issue": None,  # handled by ConversationHandler
    }

    handler = dispatch.get(cmd)
    if handler:
        # Create a pseudo-update with message context for handlers that expect update.message
        # For callback queries, we respond in the chat
        await query.message.reply_text("⏳ Loading...")
        # Re-use the handler by faking args
        context.args = []
        fake_update = update
        # Call the handler — it will use update.effective_message
        try:
            await handler(fake_update, context)
        except Exception:
            pass
    elif cmd == "create_issue":
        await query.message.reply_text(
            "💡 Use /create_issue to start the issue creation wizard."
        )


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def register_handlers(application: Application) -> None:
    """Register all handlers on the application."""

    # Basic commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("health", health))
    application.add_handler(CommandHandler("company", company))

    # Issue commands (ConversationHandlers first — higher priority)
    application.add_handler(get_create_issue_handler())
    application.add_handler(get_update_issue_handler())
    application.add_handler(CommandHandler("issues", issues))

    # Resource commands
    application.add_handler(CommandHandler("projects", projects))
    application.add_handler(CommandHandler("agents", agents))
    application.add_handler(CommandHandler("environments", environments))
    application.add_handler(CommandHandler("members", members))
    application.add_handler(CommandHandler("invites", invites))

    # Admin commands
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("broadcast", broadcast))

    # Callback query handlers for pagination & filters
    application.add_handler(
        CallbackQueryHandler(issues_pagination_callback, pattern=r"^issues:page:")
    )
    application.add_handler(
        CallbackQueryHandler(issues_filter_callback, pattern=r"^issues:filter:")
    )
    application.add_handler(
        CallbackQueryHandler(projects_pagination_callback, pattern=r"^projects:page:")
    )
    application.add_handler(
        CallbackQueryHandler(agents_pagination_callback, pattern=r"^agents:page:")
    )
    application.add_handler(
        CallbackQueryHandler(envs_pagination_callback, pattern=r"^envs:page:")
    )

    # Quick-action buttons from /start
    application.add_handler(
        CallbackQueryHandler(quick_action_callback, pattern=r"^cmd:")
    )

    # Ignore no-op buttons (page indicators)
    application.add_handler(
        CallbackQueryHandler(lambda u, c: u.callback_query.answer(), pattern=r"^noop$")
    )

    # Natural-language fallback (must be last)
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    # Scheduled digest
    schedule_digest(application)
