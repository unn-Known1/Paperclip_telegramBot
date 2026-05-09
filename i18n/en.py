"""English locale strings."""

from i18n.base import Strings

EN = Strings(
    # Auth
    unauthorized="🚫 You are not authorized to use this bot.",
    admin_only="🔒 This command is restricted to administrators.",
    rate_limited="⏳ Slow down! You're sending too many requests. Please wait a moment.",

    # Errors
    error_generic="Something went wrong. Please try again later.",
    error_api_unreachable="The Paperclip API is unreachable. Please check if the server is running.",
    error_api_timeout="The Paperclip API took too long to respond. Please try again.",
    error_not_found="The requested resource was not found.",
    error_api_unauthorized="The API rejected the request. Please check your credentials.",
    error_api_server="The Paperclip API is experiencing issues. Please try again later.",

    # Basic commands
    welcome=(
        "👋 <b>Welcome to the Paperclip Bot!</b>\n\n"
        "I help you manage your Paperclip projects right from Telegram.\n\n"
        "Tap a button below or use /help to see all commands."
    ),
    help_text=(
        "📖 <b>Available Commands</b>\n\n"
        "<b>📋 Issues</b>\n"
        "/issues — List all issues (with filters)\n"
        "/create_issue — Create a new issue\n"
        "/update_issue <code>&lt;id&gt;</code> — Update an issue\n\n"
        "<b>📁 Resources</b>\n"
        "/projects — List projects\n"
        "/agents — List agents\n"
        "/environments — List environments\n"
        "/members — List team members\n"
        "/invites — List pending invites\n\n"
        "<b>🏢 General</b>\n"
        "/company — Company details\n"
        "/health — API health status\n\n"
        "<b>🔧 Admin</b>\n"
        "/stats — Bot statistics\n"
        "/broadcast — Message all users\n\n"
        "💡 <i>You can also type natural language like</i> "
        '"show me critical bugs" <i>or</i> "create a new issue"'
    ),

    # Empty states
    no_issues="📭 No issues found.",
    no_projects="📭 No projects found.",
    no_agents="📭 No agents found.",
    no_environments="📭 No environments found.",
    no_members="📭 No members found.",
    no_invites="📭 No pending invites.",
    no_companies="📭 No companies found.",

    # Issue creation
    create_title_prompt="📝 <b>Create New Issue</b>\n\nEnter the issue <b>title</b>:",
    create_desc_prompt="📄 Now enter a <b>description</b> (or tap /skip):",
    create_priority_prompt="🎯 Select the <b>priority</b>:",
    create_project_prompt="📁 Select a <b>project</b> (or tap Skip):",
    create_agent_prompt="👤 Assign to an <b>agent</b> (or tap Skip):",
    create_confirm="✅ <b>Review your issue:</b>\n\n{details}\n\nConfirm creation?",
    create_success="🎉 Issue created successfully!\n\n{details}",
    create_cancelled="❌ Issue creation cancelled.",

    # Issue update
    update_select_field="✏️ <b>Update Issue</b>\n\n{details}\n\nSelect a field to update:",
    update_enter_value="Enter the new value for <b>{field}</b>:",
    update_success="✅ Issue updated successfully!\n\n{details}",
    update_cancelled="❌ Update cancelled.",
    update_issue_not_found="❌ Issue not found. Please check the ID.",
    update_usage="Usage: /update_issue <code>&lt;issue_id&gt;</code>",

    # Admin
    broadcast_prompt="📢 Enter the message to broadcast to all users:",
    broadcast_sent="✅ Broadcast sent to {count} user(s).",

    # Digest
    digest_header="📊 <b>Daily Digest</b> — {date}\n",
    digest_no_issues="No open issues. 🎉",

    # Misc
    unknown_command=(
        "🤔 I didn't understand that.\n\n"
        "Use /help to see available commands, or try typing naturally — "
        'for example, "show me open issues".'
    ),
    skip="Skip",
    cancel="Cancel",
    confirm="Confirm",
    back="Back",
    nlp_no_match=(
        "🤔 I couldn't figure out what you meant.\n\n"
        "Try something like:\n"
        '• "show me all issues"\n'
        '• "create a new bug"\n'
        '• "list critical tickets"\n\n'
        "Or use /help for all commands."
    ),
)
