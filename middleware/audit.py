"""Audit logging middleware — logs every command with timing."""

import functools
import logging
import time
from typing import Any

from telegram import Update
from telegram.ext import ContextTypes

audit_logger = logging.getLogger("audit")


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
            result = await func(update, context)
            elapsed_ms = (time.monotonic() - start) * 1000
            audit_logger.info(
                "command_executed",
                extra={
                    "user_id": user.id if user else 0,
                    "username": (user.username or "") if user else "",
                    "command": command,
                    "response_time_ms": round(elapsed_ms, 2),
                    "status": "success",
                },
            )
            return result
        except Exception as e:
            elapsed_ms = (time.monotonic() - start) * 1000
            audit_logger.warning(
                "command_failed",
                extra={
                    "user_id": user.id if user else 0,
                    "username": (user.username or "") if user else "",
                    "command": command,
                    "response_time_ms": round(elapsed_ms, 2),
                    "status": "error",
                    "error": str(e),
                },
            )
            raise

    return wrapper
