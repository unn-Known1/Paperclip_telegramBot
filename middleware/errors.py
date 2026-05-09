"""Global error handler — translates exceptions to user-friendly messages."""

import logging

import httpx
from telegram import Update
from telegram.ext import ContextTypes

from i18n import get_strings

logger = logging.getLogger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all unhandled exceptions raised in handlers."""
    s = get_strings()
    error = context.error

    # Full traceback for operators
    logger.error("Unhandled exception", exc_info=error)

    # Map to user-friendly message
    if isinstance(error, httpx.ConnectError):
        msg = s.error_api_unreachable
    elif isinstance(error, httpx.TimeoutException):
        msg = s.error_api_timeout
    elif isinstance(error, httpx.HTTPStatusError):
        code = error.response.status_code
        if code == 404:
            msg = s.error_not_found
        elif code in (401, 403):
            msg = s.error_api_unauthorized
        elif code >= 500:
            msg = s.error_api_server
        else:
            msg = s.error_generic
    else:
        msg = s.error_generic

    # Notify the user (best-effort)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(f"❌ {msg}")
        except Exception:
            logger.error("Failed to send error message to user")
