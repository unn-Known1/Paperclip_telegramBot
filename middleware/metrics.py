"""Prometheus metrics middleware and counters."""

import functools
import time
from typing import Any

from telegram import Update
from telegram.ext import ContextTypes

try:
    from prometheus_client import Counter, Histogram

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

# ---------------------------------------------------------------------------
# Metrics (created only when prometheus_client is installed)
# ---------------------------------------------------------------------------
if PROMETHEUS_AVAILABLE:
    COMMANDS_TOTAL = Counter(
        "bot_commands_total",
        "Total bot commands processed",
        ["command"],
    )
    ERRORS_TOTAL = Counter(
        "bot_errors_total",
        "Total errors encountered",
        ["error_type"],
    )
    RESPONSE_SECONDS = Histogram(
        "bot_response_seconds",
        "Handler response time in seconds",
        ["command"],
    )


def tracked(command_name: str):
    """Decorator that records command count, errors, and latency."""

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Any:
            if not PROMETHEUS_AVAILABLE:
                return await func(update, context)

            start = time.monotonic()
            try:
                result = await func(update, context)
                COMMANDS_TOTAL.labels(command=command_name).inc()
                return result
            except Exception as e:
                ERRORS_TOTAL.labels(error_type=type(e).__name__).inc()
                raise
            finally:
                RESPONSE_SECONDS.labels(command=command_name).observe(
                    time.monotonic() - start
                )

        return wrapper

    return decorator
