"""Issue handlers: /issues (paginated + filters), /create_issue, /update_issue."""

from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from i18n import get_strings
from middleware.auth import restricted
from middleware.audit import audited
from middleware.metrics import tracked
from middleware.rate_limit import rate_limited
from paperclip_client import get_client
from utils.chunking import send_chunked
from utils.formatting import format_issue, format_issue_detail
from utils.pagination import paginate

# ---------------------------------------------------------------------------
# ConversationHandler states for /create_issue
# ---------------------------------------------------------------------------
TITLE, DESCRIPTION, PRIORITY, PROJECT, AGENT, CONFIRM = range(6)

# ConversationHandler states for /update_issue
UPD_FIELD, UPD_VALUE = range(10, 12)


# ===================================================================
# /issues — list with inline filter buttons + pagination
# ===================================================================

@restricted
@rate_limited
@audited
@tracked("issues")
async def issues(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List issues with optional status/priority filter arguments."""
    args = context.args or []
    status = args[0] if len(args) >= 1 else None
    priority = args[1] if len(args) >= 2 else None

    client = get_client()
    s = get_strings()
    items = await client.list_issues(status=status, priority=priority)

    if not items:
        await update.message.reply_text(s.no_issues)
        return

    # Store full list for pagination
    context.user_data["issues_cache"] = items

    text, keyboard = paginate(items, page=0, prefix="issues", formatter=format_issue)

    # Add filter row
    filter_buttons = [
        InlineKeyboardButton("🟢 Open", callback_data="issues:filter:open"),
        InlineKeyboardButton("🟡 In Progress", callback_data="issues:filter:in_progress"),
        InlineKeyboardButton("🔴 Closed", callback_data="issues:filter:closed"),
        InlineKeyboardButton("📋 All", callback_data="issues:filter:all"),
    ]
    rows = [filter_buttons]
    if keyboard:
        rows.extend(keyboard.inline_keyboard)

    await update.message.reply_text(
        text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(rows)
    )


async def issues_pagination_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle page navigation for issues."""
    query = update.callback_query
    await query.answer()

    data = query.data  # e.g. "issues:page:2"
    page = int(data.split(":")[-1])

    items = context.user_data.get("issues_cache", [])
    if not items:
        await query.edit_message_text("Session expired. Use /issues again.")
        return

    text, keyboard = paginate(items, page=page, prefix="issues", formatter=format_issue)

    filter_buttons = [
        InlineKeyboardButton("🟢 Open", callback_data="issues:filter:open"),
        InlineKeyboardButton("🟡 In Progress", callback_data="issues:filter:in_progress"),
        InlineKeyboardButton("🔴 Closed", callback_data="issues:filter:closed"),
        InlineKeyboardButton("📋 All", callback_data="issues:filter:all"),
    ]
    rows = [filter_buttons]
    if keyboard:
        rows.extend(keyboard.inline_keyboard)

    await query.edit_message_text(
        text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(rows)
    )


async def issues_filter_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle inline filter buttons for issues."""
    query = update.callback_query
    await query.answer()

    status_filter = query.data.split(":")[-1]  # e.g. "open", "all"
    client = get_client()
    s = get_strings()

    status = None if status_filter == "all" else status_filter
    items = await client.list_issues(status=status)

    if not items:
        await query.edit_message_text(s.no_issues)
        return

    context.user_data["issues_cache"] = items
    text, keyboard = paginate(items, page=0, prefix="issues", formatter=format_issue)

    filter_buttons = [
        InlineKeyboardButton("🟢 Open", callback_data="issues:filter:open"),
        InlineKeyboardButton("🟡 In Progress", callback_data="issues:filter:in_progress"),
        InlineKeyboardButton("🔴 Closed", callback_data="issues:filter:closed"),
        InlineKeyboardButton("📋 All", callback_data="issues:filter:all"),
    ]
    rows = [filter_buttons]
    if keyboard:
        rows.extend(keyboard.inline_keyboard)

    await query.edit_message_text(
        text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(rows)
    )


# ===================================================================
# /create_issue — ConversationHandler wizard
# ===================================================================

@restricted
@rate_limited
@audited
@tracked("create_issue")
async def create_issue_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Step 1: ask for title."""
    s = get_strings()
    context.user_data["new_issue"] = {}
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton(f"❌ {s.cancel}", callback_data="create:cancel")]]
    )
    await update.message.reply_text(s.create_title_prompt, parse_mode="HTML", reply_markup=keyboard)
    return TITLE


async def create_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Step 2: receive title, ask for description."""
    s = get_strings()
    context.user_data["new_issue"]["title"] = update.message.text
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(f"⏭ {s.skip}", callback_data="create:skip_desc"),
                InlineKeyboardButton(f"❌ {s.cancel}", callback_data="create:cancel"),
            ]
        ]
    )
    await update.message.reply_text(s.create_desc_prompt, parse_mode="HTML", reply_markup=keyboard)
    return DESCRIPTION


async def create_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Step 3: receive description, ask for priority."""
    context.user_data["new_issue"]["description"] = update.message.text
    return await _ask_priority(update, context)


async def create_skip_desc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Skip description."""
    query = update.callback_query
    await query.answer()
    context.user_data["new_issue"]["description"] = ""
    return await _ask_priority(update, context)


async def _ask_priority(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show priority selection keyboard."""
    s = get_strings()
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🔴 Critical", callback_data="create:pri:critical"),
                InlineKeyboardButton("🟠 High", callback_data="create:pri:high"),
            ],
            [
                InlineKeyboardButton("🟡 Medium", callback_data="create:pri:medium"),
                InlineKeyboardButton("🟢 Low", callback_data="create:pri:low"),
            ],
            [InlineKeyboardButton(f"❌ {s.cancel}", callback_data="create:cancel")],
        ]
    )
    msg = update.effective_message
    if update.callback_query:
        await update.callback_query.edit_message_text(
            s.create_priority_prompt, parse_mode="HTML", reply_markup=keyboard
        )
    else:
        await msg.reply_text(s.create_priority_prompt, parse_mode="HTML", reply_markup=keyboard)
    return PRIORITY


async def create_priority(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive priority, ask for project."""
    query = update.callback_query
    await query.answer()
    priority = query.data.split(":")[-1]
    context.user_data["new_issue"]["priority"] = priority

    # Fetch projects for selection
    s = get_strings()
    client = get_client()
    try:
        projects = await client.list_projects()
    except Exception:
        projects = []

    buttons = []
    for p in projects[:10]:
        name = p.get("name", "?")[:20]
        buttons.append(
            [InlineKeyboardButton(f"📁 {name}", callback_data=f"create:proj:{p['id']}")]
        )
    buttons.append(
        [
            InlineKeyboardButton(f"⏭ {s.skip}", callback_data="create:skip_proj"),
            InlineKeyboardButton(f"❌ {s.cancel}", callback_data="create:cancel"),
        ]
    )

    await query.edit_message_text(
        s.create_project_prompt, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(buttons)
    )
    return PROJECT


async def create_project(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive project selection, ask for agent."""
    query = update.callback_query
    await query.answer()

    data = query.data
    if data == "create:skip_proj":
        context.user_data["new_issue"]["project_id"] = None
    else:
        context.user_data["new_issue"]["project_id"] = data.split(":")[-1]

    # Fetch agents
    s = get_strings()
    client = get_client()
    try:
        agents = await client.list_agents()
    except Exception:
        agents = []

    buttons = []
    for a in agents[:10]:
        name = a.get("name", "?")[:20]
        buttons.append(
            [InlineKeyboardButton(f"🤖 {name}", callback_data=f"create:agent:{a['id']}")]
        )
    buttons.append(
        [
            InlineKeyboardButton(f"⏭ {s.skip}", callback_data="create:skip_agent"),
            InlineKeyboardButton(f"❌ {s.cancel}", callback_data="create:cancel"),
        ]
    )

    await query.edit_message_text(
        s.create_agent_prompt, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(buttons)
    )
    return AGENT


async def create_agent(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive agent selection, show confirmation."""
    query = update.callback_query
    await query.answer()

    data = query.data
    if data == "create:skip_agent":
        context.user_data["new_issue"]["agent_id"] = None
    else:
        context.user_data["new_issue"]["agent_id"] = data.split(":")[-1]

    return await _show_confirm(update, context)


async def _show_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show a summary and confirm/cancel buttons."""
    s = get_strings()
    issue = context.user_data["new_issue"]

    details = (
        f"<b>Title:</b> {issue.get('title', '—')}\n"
        f"<b>Description:</b> {issue.get('description') or '—'}\n"
        f"<b>Priority:</b> {issue.get('priority', 'medium')}\n"
        f"<b>Project:</b> {issue.get('project_id') or '—'}\n"
        f"<b>Agent:</b> {issue.get('agent_id') or '—'}"
    )
    text = s.create_confirm.format(details=details)

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(f"✅ {s.confirm}", callback_data="create:confirm"),
                InlineKeyboardButton(f"❌ {s.cancel}", callback_data="create:cancel"),
            ]
        ]
    )

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text, parse_mode="HTML", reply_markup=keyboard
        )
    return CONFIRM


async def create_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Create the issue via API."""
    query = update.callback_query
    await query.answer()

    s = get_strings()
    issue = context.user_data.pop("new_issue", {})

    client = get_client()
    result = await client.create_issue(
        title=issue.get("title", "Untitled"),
        description=issue.get("description", ""),
        priority=issue.get("priority", "medium"),
        assignee_agent_id=issue.get("agent_id"),
        project_id=issue.get("project_id"),
    )

    text = s.create_success.format(details=format_issue_detail(result))
    await query.edit_message_text(text, parse_mode="HTML")
    return ConversationHandler.END


async def create_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the creation flow."""
    query = update.callback_query
    await query.answer()
    s = get_strings()
    context.user_data.pop("new_issue", None)
    await query.edit_message_text(s.create_cancelled)
    return ConversationHandler.END


# ===================================================================
# /update_issue <id> — field-select inline keyboard
# ===================================================================

@restricted
@rate_limited
@audited
@tracked("update_issue")
async def update_issue_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show issue details and field-selection keyboard."""
    s = get_strings()
    args = context.args or []
    if not args:
        await update.message.reply_text(s.update_usage, parse_mode="HTML")
        return ConversationHandler.END

    issue_id = args[0]
    client = get_client()
    try:
        issue = await client.get_issue(issue_id)
    except Exception:
        await update.message.reply_text(s.update_issue_not_found)
        return ConversationHandler.END

    context.user_data["update_issue"] = {"id": issue_id, "current": issue}

    text = s.update_select_field.format(details=format_issue_detail(issue))
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📝 Title", callback_data="upd:field:title"),
                InlineKeyboardButton("📄 Description", callback_data="upd:field:description"),
            ],
            [
                InlineKeyboardButton("🎯 Priority", callback_data="upd:field:priority"),
                InlineKeyboardButton("📊 Status", callback_data="upd:field:status"),
            ],
            [InlineKeyboardButton(f"❌ {s.cancel}", callback_data="upd:cancel")],
        ]
    )
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=keyboard)
    return UPD_FIELD


async def update_field_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User selected a field to update."""
    query = update.callback_query
    await query.answer()
    s = get_strings()

    field_name = query.data.split(":")[-1]
    context.user_data["update_issue"]["field"] = field_name

    # For priority/status, show inline options
    if field_name == "priority":
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🔴 Critical", callback_data="upd:val:critical"),
                    InlineKeyboardButton("🟠 High", callback_data="upd:val:high"),
                ],
                [
                    InlineKeyboardButton("🟡 Medium", callback_data="upd:val:medium"),
                    InlineKeyboardButton("🟢 Low", callback_data="upd:val:low"),
                ],
                [InlineKeyboardButton(f"❌ {s.cancel}", callback_data="upd:cancel")],
            ]
        )
        await query.edit_message_text(
            s.update_enter_value.format(field="priority"),
            parse_mode="HTML",
            reply_markup=keyboard,
        )
        return UPD_VALUE
    elif field_name == "status":
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🟢 Open", callback_data="upd:val:open"),
                    InlineKeyboardButton("🟡 In Progress", callback_data="upd:val:in_progress"),
                ],
                [
                    InlineKeyboardButton("🔴 Closed", callback_data="upd:val:closed"),
                ],
                [InlineKeyboardButton(f"❌ {s.cancel}", callback_data="upd:cancel")],
            ]
        )
        await query.edit_message_text(
            s.update_enter_value.format(field="status"),
            parse_mode="HTML",
            reply_markup=keyboard,
        )
        return UPD_VALUE

    # For text fields, ask user to type
    await query.edit_message_text(
        s.update_enter_value.format(field=field_name), parse_mode="HTML"
    )
    return UPD_VALUE


async def update_value_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive a text value for the field and apply the update."""
    s = get_strings()
    info = context.user_data.get("update_issue", {})
    field_name = info.get("field", "title")
    value = update.message.text

    client = get_client()
    result = await client.update_issue(info["id"], **{field_name: value})

    text = s.update_success.format(details=format_issue_detail(result))
    await send_chunked(update, text)
    context.user_data.pop("update_issue", None)
    return ConversationHandler.END


async def update_value_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive a button value for priority/status and apply the update."""
    query = update.callback_query
    await query.answer()

    s = get_strings()
    info = context.user_data.get("update_issue", {})
    field_name = info.get("field", "status")
    value = query.data.split(":")[-1]

    client = get_client()
    result = await client.update_issue(info["id"], **{field_name: value})

    text = s.update_success.format(details=format_issue_detail(result))
    await query.edit_message_text(text, parse_mode="HTML")
    context.user_data.pop("update_issue", None)
    return ConversationHandler.END


async def update_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the update flow."""
    query = update.callback_query
    await query.answer()
    s = get_strings()
    context.user_data.pop("update_issue", None)
    await query.edit_message_text(s.update_cancelled)
    return ConversationHandler.END


# ===================================================================
# Build ConversationHandlers
# ===================================================================

def get_create_issue_handler() -> ConversationHandler:
    """Return the ConversationHandler for /create_issue."""
    return ConversationHandler(
        entry_points=[CommandHandler("create_issue", create_issue_start)],
        states={
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, create_title)],
            DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, create_description),
                CallbackQueryHandler(create_skip_desc, pattern=r"^create:skip_desc$"),
            ],
            PRIORITY: [
                CallbackQueryHandler(create_priority, pattern=r"^create:pri:"),
            ],
            PROJECT: [
                CallbackQueryHandler(create_project, pattern=r"^create:(proj|skip_proj):?"),
            ],
            AGENT: [
                CallbackQueryHandler(create_agent, pattern=r"^create:(agent|skip_agent):?"),
            ],
            CONFIRM: [
                CallbackQueryHandler(create_confirm, pattern=r"^create:confirm$"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(create_cancel, pattern=r"^create:cancel$"),
            CommandHandler("cancel", lambda u, c: ConversationHandler.END),
        ],
    )


def get_update_issue_handler() -> ConversationHandler:
    """Return the ConversationHandler for /update_issue."""
    return ConversationHandler(
        entry_points=[CommandHandler("update_issue", update_issue_start)],
        states={
            UPD_FIELD: [
                CallbackQueryHandler(update_field_select, pattern=r"^upd:field:"),
            ],
            UPD_VALUE: [
                CallbackQueryHandler(update_value_button, pattern=r"^upd:val:"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, update_value_text),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(update_cancel, pattern=r"^upd:cancel$"),
            CommandHandler("cancel", lambda u, c: ConversationHandler.END),
        ],
    )
