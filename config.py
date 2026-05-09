"""Configuration loader for the Paperclip Telegram Bot."""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
PAPERCLIP_API_URL: str = os.getenv("PAPERCLIP_API_URL", "http://127.0.0.1:3100")
PAPERCLIP_COMPANY_ID: str = os.getenv("PAPERCLIP_COMPANY_ID", "")

# ---------------------------------------------------------------------------
# Access Control
# ---------------------------------------------------------------------------
_allowed = os.getenv("ALLOWED_USER_IDS", "")
ALLOWED_USER_IDS: set[int] = set()
if _allowed.strip():
    for uid in _allowed.split(","):
        uid = uid.strip()
        if uid.isdigit():
            ALLOWED_USER_IDS.add(int(uid))

_admins = os.getenv("ADMIN_USER_IDS", "")
ADMIN_USER_IDS: set[int] = set()
if _admins.strip():
    for uid in _admins.split(","):
        uid = uid.strip()
        if uid.isdigit():
            ADMIN_USER_IDS.add(int(uid))

# ---------------------------------------------------------------------------
# Webhook (leave WEBHOOK_URL empty to use polling)
# ---------------------------------------------------------------------------
WEBHOOK_URL: str = os.getenv("WEBHOOK_URL", "")
WEBHOOK_PORT: int = int(os.getenv("WEBHOOK_PORT", "8443"))
WEBHOOK_PATH: str = os.getenv("WEBHOOK_PATH", "/webhook")

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_FORMAT: str = os.getenv("LOG_FORMAT", "text")  # "text" or "json"
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

# ---------------------------------------------------------------------------
# Rate Limiting
# ---------------------------------------------------------------------------
RATE_LIMIT_RPM: int = int(os.getenv("RATE_LIMIT_RPM", "30"))

# ---------------------------------------------------------------------------
# Prometheus Metrics
# ---------------------------------------------------------------------------
METRICS_ENABLED: bool = os.getenv("METRICS_ENABLED", "false").lower() == "true"
METRICS_PORT: int = int(os.getenv("METRICS_PORT", "9090"))

# ---------------------------------------------------------------------------
# Scheduled Digest
# ---------------------------------------------------------------------------
DIGEST_ENABLED: bool = os.getenv("DIGEST_ENABLED", "false").lower() == "true"
DIGEST_HOUR: int = int(os.getenv("DIGEST_HOUR", "9"))
DIGEST_MINUTE: int = int(os.getenv("DIGEST_MINUTE", "0"))

# ---------------------------------------------------------------------------
# Internationalisation
# ---------------------------------------------------------------------------
LOCALE: str = os.getenv("LOCALE", "en")

# ---------------------------------------------------------------------------
# HTTP Client
# ---------------------------------------------------------------------------
API_TIMEOUT: float = float(os.getenv("API_TIMEOUT", "15.0"))
API_RETRIES: int = int(os.getenv("API_RETRIES", "3"))


def validate() -> None:
    """Exit with a clear message if required config is missing."""
    errors: list[str] = []
    if not TELEGRAM_BOT_TOKEN:
        errors.append("TELEGRAM_BOT_TOKEN is not set")
    if not ALLOWED_USER_IDS:
        errors.append("ALLOWED_USER_IDS is not set (no users will be allowed)")
    if errors:
        for e in errors:
            print(f"CONFIG ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    # Warnings
    if not ADMIN_USER_IDS:
        print(
            "WARNING: ADMIN_USER_IDS not set — admin commands disabled",
            file=sys.stderr,
        )
