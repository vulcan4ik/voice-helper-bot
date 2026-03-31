"""Inline button callbacks for saving notes."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot.models.voice_note import VoiceNote
from bot.services import gdrive
from bot.utils.config import Config
from bot.utils.text import chunk_text
from bot.utils.ui import build_save_keyboard


logger = logging.getLogger(__name__)


def _should_show_full(note: VoiceNote | None) -> bool:
    if note is None:
        return False
    return len(note.transcript) > 3500


async def save_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Save the last note to Google Drive based on user choice."""

    query = update.callback_query
    if query is None:
        return

    await query.answer()

    note: VoiceNote | None = context.user_data.get("last_note")
    if note is None:
        await query.edit_message_text("Нет данных для сохранения. Отправь новое аудио.")
        return

    if query.data == "show:full":
        chat_id = update.effective_chat.id if update.effective_chat else None
        for chunk in chunk_text(note.transcript):
            if query.message is not None:
                await query.message.reply_text(chunk)
            elif chat_id is not None:
                await context.bot.send_message(chat_id=chat_id, text=chunk)
        await query.edit_message_text(
            "Полный текст отправлен. Можно сохранить файл.",
            reply_markup=build_save_keyboard(show_full=_should_show_full(note)),
        )
        return

    config: Config = context.application.bot_data["config"]
    data = query.data or ""
    save_audio = data in {"save:audio", "save:audio:txt"}
    if data in {"save:txt", "save:text", "save:audio:txt"}:
        text_format = "txt"
    else:
        text_format = "md"

    try:
        link = await gdrive.save_note(note, save_audio, config, text_format)
        await query.edit_message_text(
            f"Сохранено: {link}\n\nМожно выбрать другой вариант сохранения.",
            reply_markup=build_save_keyboard(show_full=_should_show_full(note)),
        )
    except Exception as exc:
        logger.exception("Failed to save note: %s", exc)
        message = gdrive.describe_drive_error(exc)
        await query.edit_message_text(
            message or "Не удалось сохранить файл в Google Drive. Проверь настройки.",
            reply_markup=build_save_keyboard(show_full=_should_show_full(note)),
        )
