"""Tests for middleware modules."""

import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch

from middleware.rate_limit import _TokenBucket


class TestTokenBucket:
    def test_consume_within_limit(self):
        bucket = _TokenBucket(rate=10.0, capacity=10.0)
        for _ in range(10):
            assert bucket.consume() is True

    def test_consume_exceeds_limit(self):
        bucket = _TokenBucket(rate=1.0, capacity=2.0)
        assert bucket.consume() is True
        assert bucket.consume() is True
        assert bucket.consume() is False  # exhausted

    def test_refill_over_time(self):
        bucket = _TokenBucket(rate=100.0, capacity=100.0)
        # Exhaust all tokens
        for _ in range(100):
            bucket.consume()
        assert bucket.consume() is False

        # Simulate time passing
        bucket.last_refill -= 1.0  # 1 second ago
        assert bucket.consume() is True  # should have refilled
