"""Message chunking for Telegram's 4096-character limit."""

from __future__ import annotations

from telegram import Update

MAX_MESSAGE_LENGTH = 4096


def chunk_text(text: str, max_length: int = MAX_MESSAGE_LENGTH) -> list[str]:
    """Split *text* into chunks respecting line boundaries."""
    if len(text) <= max_length:
        return [text]

    chunks: list[str] = []
    while text:
        if len(text) <= max_length:
            chunks.append(text)
            break

        split_at = text.rfind("\n", 0, max_length)
        if split_at == -1:
            split_at = max_length

        chunks.append(text[:split_at])
        text = text[split_at:].lstrip("\n")

    return chunks


async def send_chunked(
    update: Update,
    text: str,
    parse_mode: str | None = "HTML",
    reply_markup=None,
) -> None:
    """Send a potentially long message as multiple Telegram messages."""
    chunks = chunk_text(text)
    for i, chunk in enumerate(chunks):
        markup = reply_markup if i == len(chunks) - 1 else None
        msg = update.effective_message
        if msg:
            await msg.reply_text(chunk, parse_mode=parse_mode, reply_markup=markup)
