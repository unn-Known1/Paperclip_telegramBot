"""Search handler: /search <query>."""

import logging

from telegram import ChatAction, Update
from telegram.ext import ContextTypes

from i18n import get_strings
from middleware.auth import restricted
from middleware.audit import audited
from middleware.metrics import tracked
from middleware.rate_limit import rate_limited
from paperclip_client import get_client
from utils.formatting import format_issue

logger = logging.getLogger(__name__)


@restricted
@rate_limited
@audited
@tracked("search")
async def search_issues(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Search issues by text."""
    s = get_strings()
    args = context.args or []
    if not args:
        await update.message.reply_text(s.search_prompt, parse_mode="HTML")
        return

    query_text = " ".join(args).lower()
    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    
    client = get_client()
    try:
        all_issues = await client.list_issues()
        matches = [
            i for i in all_issues
            if query_text in (i.get("title", "")).lower()
            or query_text in (i.get("description", "")).lower()
        ][:20]  # Show top 20
        
        if not matches:
            await update.message.reply_text(
                s.search_no_results.format(query=query_text), parse_mode="HTML"
            )
            return
            
        header = s.search_results_header.format(query=query_text)
        body = "\n\n".join(format_issue(i) for i in matches)
        await update.message.reply_text(f"{header}{body}", parse_mode="HTML")
    except Exception as e:
        logger.error("Search failed: %s", e)
        await update.message.reply_text(s.error_generic)
