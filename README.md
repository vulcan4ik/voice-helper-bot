# Проект: Telegram-бот для транскрибации голосовых сообщений

Бот принимает voice/audio, расшифровывает через Deepgram и сохраняет результат в Google Drive. Подходит для быстрых заметок: TXT для телефона, MD для структуры.

---

## ✨ Возможности
- Расшифровка аудио в текст (русский язык).
- Сохранение в Google Drive: TXT или MD, с/без аудио.
- Для длинных текстов: превью + кнопка «Показать полностью».
- Кнопки сохранения остаются доступными после операции.

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
- `DEEPGRAM_API_KEY`
- `GOOGLE_SERVICE_ACCOUNT_FILE`
- `GOOGLE_DRIVE_PARENT_ID` (опционально)
- `GOOGLE_SHARED_DRIVE_ID` (опционально)
- `GOOGLE_OAUTH_CLIENT_FILE` (опционально, для OAuth)
- `GOOGLE_OAUTH_TOKEN_FILE` (опционально, для OAuth)

Если используешь OAuth, один раз сгенерируй токен:
```bash
python scripts/google_oauth.py
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
  handlers/
  services/
  models/
  utils/
tests/
docs/
scripts/
```
