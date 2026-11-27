# AGENTS.md — voice-helper-bot

> Единственная точка входа для агентов и контрибьюторов. Этот файл читается
> автоматически (OpenCode, Codex, Cursor и др.). Меняешь структуру или правила — обнови его.

## Что это за проект

Персональный Telegram-бот для голосовых заметок:
- Голосовое/аудио -> транскрипция через Deepgram (nova-3, язык ru, диаризация спикеров)
- Кнопки сохранения в Google Drive: текст TXT/MD, аудио + текст, папки по дате
- Конспект бесед: /new -> голосовые -> /end — саммари через LLM (OpenAI-совместимый API)
- Доступ ограничен одним пользователем (ADMIN_ID)

## Стек (фактический)

- Python 3.11+, python-telegram-bot v20+ (async)
- Deepgram REST API напрямую через httpx
- Google Drive API (google-api-python-client), OAuth или service account
- LLM: OpenAI-совместимый chat completions через httpx (LLM_API_KEY / LLM_BASE_URL / LLM_MODEL)
- Деплой: Docker Compose на VM Google Cloud

## Структура

```
bot/
  main.py            # входная точка, регистрация хендлеров
  handlers/          # один файл на группу: start, media, callbacks, dialogue
  services/          # бизнес-логика без Telegram-зависимостей: deepgram, gdrive, llm, access
  models/            # датаклассы (VoiceNote)
  utils/             # конфиг, текстовые хелперы, клавиатуры
docs/
  PROJECT_CONTEXT.md # текущее состояние проекта — обновляй по итогам работы
  TASKS.md           # задачи — закрывай сделанное, добавляй новое
  DEV_RULES.md       # краткая выжимка правил (канон — здесь)
conftest.py          # делает пакет bot импортируемым для pytest
```

## Правила (обязательные)

- Код простой, без сложных паттернов; комментарии к важным шагам
- Комментарии в коде — на английском, тексты для пользователя — на русском
- logging вместо print
- Секреты только через .env (см. .env.example); .env не коммитится
- Handlers тонкие: логика живёт в services/
- Блокирующие вызовы (Google API, файлы) — через asyncio.to_thread
- Никаких секретов в конфиг-файлах (opencode.jsonc и т.п.) — только env-переменные

## Сессия агента (workflow)

Начало:
1. Прочитай docs/PROJECT_CONTEXT.md и docs/TASKS.md
2. Возьми задачу из TASKS.md (или добавь свою)

Конец:
1. Обнови docs/PROJECT_CONTEXT.md по итогам работы
2. Обнови docs/TASKS.md: закрой сделанное, добавь новое

## Тесты и проверки

- `python -m pytest tests/` — из корня проекта (conftest.py уже настроен)
- `ruff check bot tests --select F,E9` — реальные ошибки, стиль вторичен
- Новая логика в services/ -> тест в tests/

## Git и деплой

- Коммиты в императиве: "Add X", "Fix Y"
- Разработка в ветке -> PR -> merge в main
- Тег last-working — точка отката для VM
- Деплой на VM: git pull + docker compose up -d --build (автодеплой — в планах, см. docs/TASKS.md)

## Запрещено

- print() вместо logging
- time.sleep() в async-коде — только asyncio.sleep()
- bare except:
- секреты в коде или конфигах (opencode.jsonc и т.п.)
- бизнес-логика в handlers/
