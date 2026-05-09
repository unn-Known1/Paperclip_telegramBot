"""Inline query handler — search issues from any chat via @bot <query>."""

from __future__ import annotations

import logging
from uuid import uuid4

from telegram import InlineQueryResultArticle, InputTextMessageContent, Update
from telegram.ext import ContextTypes

from paperclip_client import get_client
from utils.formatting import format_issue_detail

logger = logging.getLogger(__name__)


async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline queries: @botname <search text>."""
    query_text = update.inline_query.query.strip()
    if not query_text or len(query_text) < 2:
        return

    client = get_client()
    try:
        all_issues = await client.list_issues()
    except Exception as e:
        logger.warning("Inline query failed: %s", e)
        return

    # Simple text search across title and description
    lower_q = query_text.lower()
    matches = [
        i for i in all_issues
        if lower_q in (i.get("title", "")).lower()
        or lower_q in (i.get("description", "")).lower()
    ][:10]  # Telegram allows max 50, we cap at 10

    results = []
    for issue in matches:
        title = issue.get("title", "Untitled")
        status = issue.get("status", "unknown")
        priority = issue.get("priority", "—")
        detail_text = format_issue_detail(issue)

        results.append(
            InlineQueryResultArticle(
                id=str(uuid4()),
                title=f"{title}",
                description=f"{status.capitalize()} • {priority.capitalize()}",
                input_message_content=InputTextMessageContent(
                    detail_text, parse_mode="HTML"
                ),
            )
        )

    await update.inline_query.answer(results, cache_time=30)
