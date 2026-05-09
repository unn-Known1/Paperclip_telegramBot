"""Per-user token-bucket rate limiter."""

import functools
import time
from typing import Any

from telegram import Update
from telegram.ext import ContextTypes

import config
from i18n import get_strings


class _TokenBucket:
    """Simple token-bucket implementation."""

    __slots__ = ("rate", "capacity", "tokens", "last_refill")

    def __init__(self, rate: float, capacity: float):
        self.rate = rate  # tokens per second
        self.capacity = capacity
        self.tokens = capacity
        self.last_refill = time.monotonic()

    def consume(self) -> bool:
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_refill = now
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False


_buckets: dict[int, _TokenBucket] = {}


def _get_bucket(user_id: int) -> _TokenBucket:
    if user_id not in _buckets:
        rpm = config.RATE_LIMIT_RPM
        _buckets[user_id] = _TokenBucket(rate=rpm / 60.0, capacity=float(rpm))
    return _buckets[user_id]


def rate_limited(func):
    """Reject requests that exceed the per-user rate limit."""

    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Any:
        user = update.effective_user
        if user and not _get_bucket(user.id).consume():
            s = get_strings()
            if update.message:
                await update.message.reply_text(s.rate_limited)
            elif update.callback_query:
                await update.callback_query.answer(s.rate_limited, show_alert=True)
            return
        return await func(update, context)

    return wrapper
