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
from bot.services.access import is_allowed_user
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

    audio = message.voice or message.audio
    if audio is None:
        return

    config: Config = context.application.bot_data["config"]
    user_id = update.effective_user.id if update.effective_user else None
    if not is_allowed_user(user_id, config.admin_id):
        await message.reply_text("Доступ к боту ограничен.")
        return

    local_path: Path | None = None
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
        # Remove the downloaded file so failed runs don't fill up the disk.
        if local_path is not None:
            try:
                local_path.unlink(missing_ok=True)
            except OSError:
                logger.warning("Failed to remove temp file: %s", local_path)
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

    # When a dialogue is active (/new), the transcript is added to it.
    dialogue_note = ""
    dialogue: list[str] | None = context.chat_data.get("dialogue")
    if dialogue is not None:
        dialogue.append(transcript)
        dialogue_note = (
            f"\n\nДобавлено в беседу (сообщений: {len(dialogue)}). /end — собрать конспект."
        )

    is_long = len(transcript) > TELEGRAM_SAFE_LIMIT
    keyboard = build_save_keyboard(show_full=is_long)

    if is_long:
        preview = make_preview(transcript)
        await message.reply_text(
            f"Текст длинный, показан фрагмент:\n\n{preview}"
        )
        await message.reply_text(f"Что сделать дальше?{dialogue_note}", reply_markup=keyboard)
        return

    await message.reply_text(transcript)
    await message.reply_text(f"Что сделать дальше?{dialogue_note}", reply_markup=keyboard)
