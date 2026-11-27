"""Handlers for dialogue conspects: /new, /status, /end."""

from __future__ import annotations

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from bot.services import llm
from bot.services.access import is_allowed_user
from bot.utils.config import Config
from bot.utils.text import chunk_text


logger = logging.getLogger(__name__)


async def new_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start a new dialogue: voice transcripts get collected into it."""

    if update.message is None:
        return

    config: Config = context.application.bot_data["config"]
    user_id = update.effective_user.id if update.effective_user else None
    if not is_allowed_user(user_id, config.admin_id):
        await update.message.reply_text("Доступ к боту ограничен.")
        return

    context.chat_data["dialogue"] = []
    await update.message.reply_text(
        "Беседа начата. Присылай голосовые — транскрипты будут складываться в диалог. "
        "Команда /end соберёт конспект."
    )


async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show how many voice messages are collected in the dialogue."""

    if update.message is None:
        return

    config: Config = context.application.bot_data["config"]
    user_id = update.effective_user.id if update.effective_user else None
    if not is_allowed_user(user_id, config.admin_id):
        await update.message.reply_text("Доступ к боту ограничен.")
        return

    dialogue = context.chat_data.get("dialogue")
    if dialogue is None:
        await update.message.reply_text("Беседа не активна. /new — начать новую.")
    else:
        await update.message.reply_text(
            f"В беседе {len(dialogue)} голосовых. /end — собрать конспект."
        )


async def end_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Summarize the dialogue with LLM and offer to save the conspect."""

    if update.message is None:
        return

    config: Config = context.application.bot_data["config"]
    user_id = update.effective_user.id if update.effective_user else None
    if not is_allowed_user(user_id, config.admin_id):
        await update.message.reply_text("Доступ к боту ограничен.")
        return

    dialogue: list[str] = context.chat_data.get("dialogue") or []
    if not dialogue:
        await update.message.reply_text(
            "В беседе пока нет голосовых. Отправь голосовые сообщения или начни новую командой /new."
        )
        return

    await update.message.reply_text("Собираю конспект, это может занять пару минут…")

    numbered = "\n\n".join(
        f"{i}. {transcript}" for i, transcript in enumerate(dialogue, start=1)
    )

    try:
        conspect = await llm.summarize_dialogue(numbered, config)
    except Exception as exc:
        logger.exception("Failed to summarize dialogue: %s", exc)
        # Dialogue is kept, so /end can be retried.
        await update.message.reply_text("Не удалось собрать конспект. Попробуй ещё раз чуть позже.")
        return

    # Dialogue is finished: keep the conspect for save buttons, clear the list.
    context.chat_data["last_conspect"] = conspect
    context.chat_data["dialogue"] = []

    # Conspect goes to the chat in full; long text is split into chunks.
    for chunk in chunk_text(conspect):
        await update.message.reply_text(chunk)

    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Сохранить конспект (TXT)", callback_data="savecons:txt")],
            [InlineKeyboardButton("Сохранить конспект (MD)", callback_data="savecons:md")],
        ]
    )
    await update.message.reply_text("Куда сохранить конспект?", reply_markup=keyboard)
