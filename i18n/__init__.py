"""Internationalisation helpers."""

from i18n.base import Strings
from i18n.en import EN

import config

_LOCALES: dict[str, Strings] = {
    "en": EN,
}

_current: Strings | None = None


def get_strings() -> Strings:
    """Return the active locale's strings (cached)."""
    global _current
    if _current is None:
        _current = _LOCALES.get(config.LOCALE, EN)
    return _current
