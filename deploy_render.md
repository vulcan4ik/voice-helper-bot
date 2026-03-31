# План деплоя на Render

## 1) Подготовка репозитория
- Убедиться, что `.env` и `token.json` не коммитятся.
- В репозитории должен быть `requirements.txt`.
- Точка входа: `python -m bot.main`.

## 2) Создать сервис на Render
1. В Render выбрать **New +** → **Background Worker** (не Web Service).
2. Подключить репозиторий с проектом.
3. Runtime: **Python**.
4. Build Command:
   - `pip install -r requirements.txt`
5. Start Command:
   - `python -m bot.main`

## 3) Переменные окружения (Secrets)
Добавить в Render → Environment:
- `BOT_TOKEN`
- `DEEPGRAM_API_KEY`
- `GOOGLE_SERVICE_ACCOUNT_FILE`
- `GOOGLE_DRIVE_PARENT_ID` (если используешь папку)
- `GOOGLE_SHARED_DRIVE_ID` (если используешь Shared Drive)
- `GOOGLE_OAUTH_CLIENT_FILE` (если используешь OAuth)
- `GOOGLE_OAUTH_TOKEN_FILE` (если используешь OAuth)

Важно: не хранить ключи в коде. Все секреты — только в Render Environment.

## 4) Файлы Google (OAuth/Service Account)
### Вариант A — Service Account (рекомендуется для сервера)
1. Скачай JSON сервисного аккаунта.
2. На Render добавь **Secret File** и загрузи JSON.
3. В `GOOGLE_SERVICE_ACCOUNT_FILE` укажи путь к загруженному secret файлу.
4. Дай сервисному аккаунту доступ к папке/Shared Drive.

### Вариант B — OAuth
1. Токен `token.json` должен храниться как Secret File.
2. Укажи `GOOGLE_OAUTH_CLIENT_FILE` и `GOOGLE_OAUTH_TOKEN_FILE` как пути к secret файлам.
3. Убедись, что токен выдан пользователем, имеющим доступ к папке.

## 5) Проверка
- Запусти деплой.
- В логах Render убедись, что бот стартует без ошибок.
- Проверь обработку аудио и сохранение в Drive.

## 6) Обслуживание
- Render автоматически перезапускает воркер при падении.
- Следи за логами на ошибки Drive/Deepgram.
- При ротации токенов обновляй переменные окружения.
