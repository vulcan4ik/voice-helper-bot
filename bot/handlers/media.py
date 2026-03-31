"""Handlers for voice messages and audio files."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
import tempfile
from uuid import uuid4

from telegram import Update
from telegram.ext import ContextTypes

from bot.models.voice_note import VoiceNote
from bot.services import deepgram
from bot.utils.config import Config
from bot.utils.text import make_preview
from bot.utils.ui import build_save_keyboard


logger = logging.getLogger(__name__)

MIME_BY_SUFFIX = {
    ".ogg": "audio/ogg",
    ".oga": "audio/ogg",
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".m4a": "audio/mp4",
}

TELEGRAM_SAFE_LIMIT = 3500


def _chunk_text(text: str, max_len: int = 3500) -> list[str]:
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


def _guess_mime_type(file_path: Path, fallback: str | None) -> str:
    """Pick the best mime type we can, based on suffix or metadata."""

    if fallback:
        return fallback
    return MIME_BY_SUFFIX.get(file_path.suffix.lower(), "audio/ogg")


async def media_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Download audio, send it to Deepgram, and show save buttons."""

    message = update.effective_message
    if message is None:
        return

    is_voice = message.voice is not None
    audio = message.voice or message.audio
    if audio is None:
        return

    config: Config = context.application.bot_data["config"]

    try:
        telegram_file = await context.bot.get_file(audio.file_id)
        suffix = Path(telegram_file.file_path or "").suffix or ".ogg"
        temp_dir = Path(tempfile.gettempdir()) / "voice_helper"
        temp_dir.mkdir(parents=True, exist_ok=True)
        local_path = temp_dir / f"{uuid4().hex}{suffix}"

        # Downloading to disk lets us reuse the file for saving to Drive later.
        await telegram_file.download_to_drive(custom_path=str(local_path))

        mime_type = _guess_mime_type(local_path, getattr(audio, "mime_type", None))
        transcript = await deepgram.transcribe_file(
            file_path=local_path,
            mime_type=mime_type,
            api_key=config.deepgram_api_key,
        )

    except Exception as exc:
        logger.exception("Failed to process audio: %s", exc)
        await message.reply_text(
            "Не удалось обработать аудио. Попробуй ещё раз чуть позже."
        )
        return

    previous_note: VoiceNote | None = context.user_data.get("last_note")
    if previous_note is not None:
        try:
            if previous_note.file_path.exists():
                previous_note.file_path.unlink()
        except OSError:
            logger.warning("Failed to remove temp file: %s", previous_note.file_path)

    note = VoiceNote(
        transcript=transcript,
        file_path=local_path,
        original_filename=getattr(audio, "file_name", None) or "voice.ogg",
        mime_type=mime_type,
        created_at=datetime.now(),
    )
    context.user_data["last_note"] = note

    is_long = len(transcript) > TELEGRAM_SAFE_LIMIT
    keyboard = build_save_keyboard(show_full=is_long)

    if is_long:
        preview = make_preview(transcript)
        await message.reply_text(
            f"Текст длинный, показан фрагмент:\n\n{preview}"
        )
        await message.reply_text("Что сделать дальше?", reply_markup=keyboard)
        return

    await message.reply_text(transcript)
    await message.reply_text("Что сделать дальше?", reply_markup=keyboard)
