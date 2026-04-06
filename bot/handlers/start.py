"""/start command handler."""

from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from bot.services.access import is_allowed_user
from bot.utils.config import Config

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Explain how to use the bot."""

    if update.message is None:
        return

    config: Config = context.application.bot_data["config"]
    user_id = update.effective_user.id if update.effective_user else None
    if not is_allowed_user(user_id, config.admin_id):
        await update.message.reply_text("Доступ к боту ограничен.")
        return

    await update.message.reply_text(
        "Привет! Отправь голосовое сообщение или аудиофайл, "
        "я сделаю транскрипцию и предложу сохранить результат."
    )
