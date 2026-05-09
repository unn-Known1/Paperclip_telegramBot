"""Shared test fixtures."""

import os
import pytest
import pytest_asyncio

# Ensure config loads test-safe defaults before any import
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token-000")
os.environ.setdefault("ALLOWED_USER_IDS", "111,222")
os.environ.setdefault("ADMIN_USER_IDS", "111")
os.environ.setdefault("PAPERCLIP_API_URL", "http://localhost:9999")
os.environ.setdefault("METRICS_ENABLED", "false")
os.environ.setdefault("DIGEST_ENABLED", "false")
