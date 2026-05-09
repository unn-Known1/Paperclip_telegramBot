"""Scheduled digest — daily summary of open issues."""

from __future__ import annotations

import datetime
import logging

from telegram.ext import ContextTypes

import config
from i18n import get_strings
from paperclip_client import get_client
from utils.formatting import format_issue

logger = logging.getLogger(__name__)


async def send_daily_digest(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Job callback: send a digest of open issues to all allowed users."""
    s = get_strings()
    client = get_client()

    try:
        issues = await client.list_issues(status="open")
    except Exception as e:
        logger.error("Digest: failed to fetch issues: %s", e)
        return

    today = datetime.date.today().strftime("%Y-%m-%d")
    header = s.digest_header.format(date=today)

    if not issues:
        text = f"{header}\n{s.digest_no_issues}"
    else:
        body = "\n\n".join(format_issue(i) for i in issues[:20])
        total = len(issues)
        footer = f"\n\n📄 Showing {min(20, total)}/{total} open issues."
        text = f"{header}\n{body}{footer}"

    for user_id in config.ALLOWED_USER_IDS:
        try:
            await context.bot.send_message(
                chat_id=user_id, text=text, parse_mode="HTML"
            )
        except Exception as e:
            logger.warning("Digest: failed to message user %s: %s", user_id, e)


def schedule_digest(application) -> None:
    """Register the daily digest job if enabled."""
    if not config.DIGEST_ENABLED:
        return

    job_queue = application.job_queue
    target_time = datetime.time(
        hour=config.DIGEST_HOUR, minute=config.DIGEST_MINUTE
    )
    job_queue.run_daily(send_daily_digest, time=target_time, name="daily_digest")
    logger.info("Digest scheduled at %s daily", target_time)
