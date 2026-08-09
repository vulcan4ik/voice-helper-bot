# Проект: Telegram-бот для транскрибации голосовых сообщений

Бот принимает voice/audio, расшифровывает через Deepgram и сохраняет результат в Google Drive. Подходит для быстрых заметок: TXT для телефона, MD для структуры.

---

## ✨ Возможности
- Расшифровка аудио в текст (русский язык).
- Сохранение в Google Drive: TXT или MD, с/без аудио.
- Для длинных текстов: превью + кнопка «Показать полностью».
- Кнопки сохранения остаются доступными после операции.
- Доступ к боту ограничен по `ADMIN_ID`.

---

## ✅ Результат
- Автоматическая транскрибация и удобное сохранение без ручной копипасты.
- Быстрый доступ к текстам в Drive с телефона и ПК.
- Минимум ручной рутины.

---

## 🚀 Быстрый старт

1) Установить зависимости:
```bash
pip install -r requirements.txt
```

2) Создать `.env` и заполнить ключи:
```bash
cp .env.example .env
```

3) Запуск:
```bash
python -m bot.main
```

---

## 🔐 Переменные окружения
- `BOT_TOKEN`
- `ADMIN_ID`
- `DEEPGRAM_API_KEY`
- `GOOGLE_SERVICE_ACCOUNT_FILE`
- `GOOGLE_DRIVE_PARENT_ID` (опционально)
- `GOOGLE_SHARED_DRIVE_ID` (опционально)
- `GOOGLE_OAUTH_CLIENT_FILE` (опционально, для OAuth)
- `GOOGLE_OAUTH_TOKEN_FILE` (опционально, для OAuth)
- `GOOGLE_OAUTH_CLIENT_JSON` (опционально, для OAuth через env)
- `GOOGLE_OAUTH_TOKEN_JSON` (опционально, для OAuth через env)

Если используешь OAuth, один раз сгенерируй токен:
```bash
python scripts/google_oauth.py
```

### Railway (OAuth через env)
Если в деплое нет файлового доступа, можно передать JSON через env и записать их при старте:

```
GOOGLE_OAUTH_CLIENT_FILE=/app/credentials/client_secret.json
GOOGLE_OAUTH_TOKEN_FILE=/app/credentials/token.json
GOOGLE_OAUTH_CLIENT_JSON=<весь JSON клиента>
GOOGLE_OAUTH_TOKEN_JSON=<весь JSON токена>
```

---

## 🧪 Тесты
```bash
pytest tests/
```

---

## 🧰 Стек
- Python 3.11+
- python-telegram-bot (async)
- Deepgram API
- Google Drive API

---

## 📂 Структура проекта
```text
bot/
  handlers/        # Telegram handlers (команды, callback, медиа)
  services/        # Бизнес-логика (Deepgram, Google Drive)
  models/          # Датаклассы и модели
  utils/           # Хелперы, конфиг, UI-клавиатуры
docs/              # Контекст проекта и правила
scripts/           # Вспомогательные скрипты (OAuth, утилиты)
tests/             # Тесты
```



### Скрипты
- `scripts/google_oauth.py` — генерация OAuth токена для Google Drive
