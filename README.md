# Telegram Voice Notes Bot

This bot transcribes voice messages and audio files using Deepgram and lets you save results to Google Drive.

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Create environment file:

```bash
cp .env.example .env
```

3. Fill in `.env` with:

- `BOT_TOKEN`
- `DEEPGRAM_API_KEY`
- `GOOGLE_SERVICE_ACCOUNT_FILE`
- `GOOGLE_DRIVE_PARENT_ID` (optional)
- `GOOGLE_SHARED_DRIVE_ID` (optional, for Shared Drive)
- `GOOGLE_OAUTH_CLIENT_FILE` (optional, for OAuth)
- `GOOGLE_OAUTH_TOKEN_FILE` (optional, for OAuth)

If you use OAuth, generate the token once:

```bash
python scripts/google_oauth.py
```

## Run

```bash
python -m bot.main
```

## Tests

```bash
pytest
```
