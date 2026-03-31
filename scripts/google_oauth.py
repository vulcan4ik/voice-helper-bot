"""Generate OAuth token for Google Drive."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow


logger = logging.getLogger(__name__)


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing {name} in environment")
    return value


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    load_dotenv()

    client_file = Path(_require_env("GOOGLE_OAUTH_CLIENT_FILE"))
    token_env = os.getenv("GOOGLE_OAUTH_TOKEN_FILE")
    token_file = Path(token_env) if token_env else client_file.with_name("token.json")

    if not client_file.exists():
        raise RuntimeError(f"OAuth client file not found: {client_file}")

    scopes = ["https://www.googleapis.com/auth/drive.file"]
    flow = InstalledAppFlow.from_client_secrets_file(str(client_file), scopes=scopes)
    credentials = flow.run_local_server(port=0)

    token_file.write_text(credentials.to_json(), encoding="utf-8")
    logger.info("Saved OAuth token to %s", token_file)


if __name__ == "__main__":
    main()
