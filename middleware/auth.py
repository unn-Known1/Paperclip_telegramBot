"""Authentication and authorisation decorators."""

import functools
from typing import Any

from telegram import Update
from telegram.ext import ContextTypes

import config
from i18n import get_strings


def restricted(func):
    """Restrict bot access to allowed users only."""

    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Any:
        user = update.effective_user
        if not user or user.id not in config.ALLOWED_USER_IDS:
            s = get_strings()
            if update.message:
                await update.message.reply_text(s.unauthorized)
            elif update.callback_query:
                await update.callback_query.answer(s.unauthorized, show_alert=True)
            return
        return await func(update, context)

    return wrapper


def admin_only(func):
    """Restrict access to admin users (must also be in ALLOWED_USER_IDS)."""

    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Any:
        user = update.effective_user
        if not user or user.id not in config.ADMIN_USER_IDS:
            s = get_strings()
            if update.message:
                await update.message.reply_text(s.admin_only)
            elif update.callback_query:
                await update.callback_query.answer(s.admin_only, show_alert=True)
            return
        return await func(update, context)

    return wrapper
