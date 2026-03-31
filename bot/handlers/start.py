"""/start command handler."""

from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Explain how to use the bot."""

    if update.message is None:
        return

    await update.message.reply_text(
        "Привет! Отправь голосовое сообщение или аудиофайл, "
        "я сделаю транскрипцию и предложу сохранить результат."
    )
