"""Bot entry point."""

from __future__ import annotations

import logging

from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from bot.handlers.callbacks import save_callback_handler
from bot.handlers.dialogue import end_handler, new_handler, status_handler
from bot.handlers.media import media_handler
from bot.handlers.start import start_handler
from bot.utils.config import load_config


def main() -> None:
    """Configure and run the bot."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)

    config = load_config()
    application = Application.builder().token(config.bot_token).build()
    application.bot_data["config"] = config

    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("new", new_handler))
    application.add_handler(CommandHandler("status", status_handler))
    application.add_handler(CommandHandler("end", end_handler))
    application.add_handler(
        MessageHandler(filters.VOICE | filters.AUDIO, media_handler)
    )
    application.add_handler(CallbackQueryHandler(save_callback_handler, pattern=r"^save:"))
    application.add_handler(CallbackQueryHandler(save_callback_handler, pattern=r"^savecons:"))
    application.add_handler(CallbackQueryHandler(save_callback_handler, pattern=r"^show:"))

    application.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
