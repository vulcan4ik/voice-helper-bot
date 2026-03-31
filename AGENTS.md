# AGENTS.md — Python Telegram Bot

## Project Overview
This is a Python-based Telegram bot project. All AI agents and contributors must follow these rules strictly.

---

## Tech Stack
- **Language:** Python 3.11+
- **Bot Framework:** `python-telegram-bot` v20+ (async)
- **Environment:** `python-dotenv` for secrets
- **Linting:** `ruff` or `flake8`
- **Testing:** `pytest` + `pytest-asyncio`
- **Dependency management:** `pip` + `requirements.txt` or `poetry`

---

## Project Structure
```
project/
├── bot/
│   ├── __init__.py
│   ├── main.py          # Entry point, Application setup
│   ├── handlers/        # One file per handler group
│   │   ├── __init__.py
│   │   ├── start.py
│   │   ├── commands.py
│   │   └── callbacks.py
│   ├── services/        # Business logic (no Telegram deps here)
│   │   └── __init__.py
│   ├── models/          # Data models / dataclasses
│   │   └── __init__.py
│   └── utils/           # Helper functions
│       └── __init__.py
├── tests/
│   ├── test_handlers.py
│   └── test_services.py
├── .env                 # Never commit this
├── .env.example
├── requirements.txt
├── AGENTS.md
└── README.md
```

---

## Coding Rules

### General
- Use **async/await** everywhere — python-telegram-bot v20+ is fully async
- Follow **PEP 8** and use type hints on all functions
- Keep handlers thin — delegate logic to `services/`
- Never hardcode secrets — always use `os.getenv()` or `.env`
- All strings in English (code) or Russian (user-facing messages) — be consistent

### Naming Conventions
- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`

### Handler Pattern
```python
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    user = update.effective_user
    await update.message.reply_text(f"Привет, {user.first_name}!")
```

### Error Handling
- Always wrap API calls in try/except
- Use `ApplicationHandlerStop` to stop handler chains when needed
- Log all errors with `logging` module, never use `print()`

```python
import logging
logger = logging.getLogger(__name__)

try:
    result = await some_api_call()
except TelegramError as e:
    logger.error(f"Telegram error: {e}")
```

---

## Environment Variables
```env
BOT_TOKEN=your_bot_token_here
ADMIN_ID=123456789
DATABASE_URL=sqlite:///bot.db  # optional
```

Never commit `.env` — only `.env.example` goes to git.

---

## Testing Rules
- Write tests for all service functions
- Mock Telegram objects using `python-telegram-bot` test utilities
- Run tests before every commit: `pytest tests/`
- Minimum coverage: 70%

---

## Git Rules
- Commit messages in imperative: `Add start handler`, `Fix callback bug`
- One feature per branch
- Never commit `.env`, `__pycache__`, `.pyc` files
- Always run `ruff check .` before committing

---

## Forbidden
- ❌ No `time.sleep()` — use `asyncio.sleep()`
- ❌ No blocking I/O in handlers — use async libraries
- ❌ No hardcoded tokens or passwords
- ❌ No business logic inside handler functions
- ❌ No `print()` for debugging — use `logging`
- ❌ No bare `except:` — always specify exception type

---

## Recommended Libraries
| Purpose | Library |
|---------|---------|
| Telegram API | `python-telegram-bot>=20.0` |
| HTTP requests | `httpx` (async) |
| Database | `aiosqlite` or `sqlalchemy[asyncio]` |
| Validation | `pydantic` |
| Scheduling | `APScheduler` |
| Config | `python-dotenv` |

---

## Running the Bot
```bash
# Install dependencies
pip install -r requirements.txt

# Copy and fill env
cp .env.example .env

# Run
python -m bot.main
```

---

## Agent Instructions
When implementing features:
1. **Always check** if a handler for this command already exists
2. **Add handler** in `bot/handlers/` — one file per logical group
3. **Register handler** in `bot/main.py` in the Application setup
4. **Write test** in `tests/` for any new service function
5. **Update** `README.md` if adding new commands
6. **Never modify** `.env` — only `.env.example`
