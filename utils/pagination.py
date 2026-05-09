"""Generic paginated list with inline-keyboard navigation."""

from __future__ import annotations

import math
from typing import Callable

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

PAGE_SIZE = 10


def paginate(
    items: list,
    page: int,
    prefix: str,
    formatter: Callable,
    page_size: int = PAGE_SIZE,
) -> tuple[str, InlineKeyboardMarkup | None]:
    """Return (formatted_text, keyboard | None) for the requested page.

    ``prefix`` is used to namespace callback data, e.g. ``"issues"``
    produces callback data like ``"issues:page:2"``.
    """
    if not items:
        return "", None

    total_pages = max(1, math.ceil(len(items) / page_size))
    page = max(0, min(page, total_pages - 1))

    start = page * page_size
    page_items = items[start : start + page_size]

    text = "\n\n".join(formatter(item) for item in page_items)

    # Page indicator
    if total_pages > 1:
        text += f"\n\n📄 Page {page + 1}/{total_pages} ({len(items)} total)"

    # Navigation keyboard
    if total_pages <= 1:
        return text, None

    buttons: list[InlineKeyboardButton] = []
    if page > 0:
        buttons.append(
            InlineKeyboardButton("◀ Prev", callback_data=f"{prefix}:page:{page - 1}")
        )
    buttons.append(
        InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="noop")
    )
    if page < total_pages - 1:
        buttons.append(
            InlineKeyboardButton("Next ▶", callback_data=f"{prefix}:page:{page + 1}")
        )

    return text, InlineKeyboardMarkup([buttons])
