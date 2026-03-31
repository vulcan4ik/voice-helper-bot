"""Text helpers for Telegram messages."""

from __future__ import annotations


def chunk_text(text: str, max_len: int = 3500) -> list[str]:
    """Split text into chunks that fit into Telegram messages."""

    if len(text) <= max_len:
        return [text]

    chunks: list[str] = []
    paragraphs = text.split("\n\n")
    for paragraph in paragraphs:
        if not paragraph:
            continue
        if len(paragraph) <= max_len:
            if chunks and len(chunks[-1]) + 2 + len(paragraph) <= max_len:
                chunks[-1] += f"\n\n{paragraph}"
            else:
                chunks.append(paragraph)
            continue

        start = 0
        while start < len(paragraph):
            chunks.append(paragraph[start : start + max_len])
            start += max_len

    return chunks


def make_preview(text: str, max_len: int = 800) -> str:
    """Return a short preview for long transcripts."""

    if len(text) <= max_len:
        return text
    return f"{text[:max_len].rstrip()}..."
