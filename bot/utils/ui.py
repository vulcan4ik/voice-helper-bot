"""UI helpers for inline keyboards."""

from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def build_save_keyboard(show_full: bool) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton("Сохранить текст (TXT)", callback_data="save:txt")],
        [InlineKeyboardButton("Сохранить текст (MD)", callback_data="save:md")],
        [
            InlineKeyboardButton(
                "Сохранить аудио + текст (MD)", callback_data="save:audio"
            )
        ],
        [
            InlineKeyboardButton(
                "Сохранить аудио + текст (TXT)", callback_data="save:audio:txt"
            )
        ],
    ]

    if show_full:
        rows.append(
            [InlineKeyboardButton("Показать полностью", callback_data="show:full")]
        )

    return InlineKeyboardMarkup(rows)
