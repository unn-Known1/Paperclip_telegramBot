"""Audit logging middleware — logs every command with timing."""

from collections import deque
import functools
import logging
import time
from datetime import datetime
from typing import Any

from telegram import Update
from telegram.ext import ContextTypes

audit_logger = logging.getLogger("audit")

# Rolling buffer of the last 50 bot activities
recent_activities = deque(maxlen=50)


def audited(func):
    """Log every invocation with user info, command, and response time."""

    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Any:
        user = update.effective_user
        start = time.monotonic()
        command = ""
        if update.message and update.message.text:
            command = update.message.text
        elif update.callback_query and update.callback_query.data:
            command = f"callback:{update.callback_query.data}"

        try:
            from handlers.admin import increment_command_count
            increment_command_count()
            
            result = await func(update, context)
            elapsed_ms = (time.monotonic() - start) * 1000
            
            activity = {
                "timestamp": datetime.now().isoformat(),
                "user_id": user.id if user else 0,
                "username": (user.username or "") if user else "",
                "command": command,
                "response_time_ms": round(elapsed_ms, 2),
                "status": "success",
            }
            recent_activities.append(activity)

            audit_logger.info(
                "command_executed",
                extra=activity,
            )
            return result
        except Exception as e:
            elapsed_ms = (time.monotonic() - start) * 1000
            
            activity = {
                "timestamp": datetime.now().isoformat(),
                "user_id": user.id if user else 0,
                "username": (user.username or "") if user else "",
                "command": command,
                "response_time_ms": round(elapsed_ms, 2),
                "status": "error",
                "error": str(e),
            }
            recent_activities.append(activity)

            audit_logger.warning(
                "command_failed",
                extra=activity,
            )
            raise

    return wrapper
