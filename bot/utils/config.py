"""Configuration loader for the bot."""

from __future__ import annotations

from dataclasses import dataclass
import os

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    """Typed configuration loaded from environment variables."""

    bot_token: str
    admin_id: int
    deepgram_api_key: str
    google_service_account_file: str
    google_drive_parent_id: str | None
    google_shared_drive_id: str | None
    google_oauth_client_file: str | None
    google_oauth_token_file: str | None


def load_config() -> Config:
    """Load configuration and fail fast if required values are missing."""

    # Load variables from .env for local development.
    load_dotenv()

    def require(name: str) -> str:
        value = os.getenv(name)
        if not value:
            raise ValueError(f"Missing required environment variable: {name}")
        return value

    def require_int(name: str) -> int:
        value = require(name)
        try:
            return int(value)
        except ValueError as exc:
            raise ValueError(f"{name} must be an integer") from exc

    google_oauth_client_file = os.getenv("GOOGLE_OAUTH_CLIENT_FILE") or None
    if google_oauth_client_file:
        google_service_account_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "")
    else:
        google_service_account_file = require("GOOGLE_SERVICE_ACCOUNT_FILE")

    return Config(
        bot_token=require("BOT_TOKEN"),
        admin_id=require_int("ADMIN_ID"),
        deepgram_api_key=require("DEEPGRAM_API_KEY"),
        google_service_account_file=google_service_account_file,
        google_drive_parent_id=os.getenv("GOOGLE_DRIVE_PARENT_ID"),
        google_shared_drive_id=os.getenv("GOOGLE_SHARED_DRIVE_ID"),
        google_oauth_client_file=google_oauth_client_file,
        google_oauth_token_file=os.getenv("GOOGLE_OAUTH_TOKEN_FILE") or None,
    )
