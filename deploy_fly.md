# Деплой на Fly.io

Бот работает через **polling** (не webhook), поэтому HTTP-порт не нужен —
Fly просто держит процесс живым. В `fly.toml` секции `[http_service]` нет.

Подготовленные файлы: `Dockerfile`, `fly.toml`, `entrypoint.sh`, `.dockerignore`.

## 1) Установить flyctl и залогиниться

На Windows — через WSL или PowerShell (инструкция на https://fly.io/docs/flyctl/install/):

```bash
fly auth login
```

## 2) Клонировать репозиторий и зайти в папку

```bash
git clone https://github.com/vulcan4ik/voice-helper-bot.git
cd voice-helper-bot
```

## 3) Создать приложение

```bash
fly launch --no-deploy
```

`fly.toml` уже есть — согласись использовать его. Если имя `voice-helper-bot`
занято, поправь `app` в `fly.toml` на другое уникальное.

## 4) Задать секреты

Проект использует **OAuth через env** (не service account): при старте бот сам
записывает `GOOGLE_OAUTH_CLIENT_JSON` и `GOOGLE_OAUTH_TOKEN_JSON` в файлы
`/app/credentials/`. Подготовь файл `deploy-fly.env` рядом с репозиторием:

```
BOT_TOKEN=<из .env>
ADMIN_ID=<из .env>
DEEPGRAM_API_KEY=<из .env>
GOOGLE_DRIVE_PARENT_ID=<из .env>
GOOGLE_OAUTH_CLIENT_FILE=/app/credentials/client_secret.json
GOOGLE_OAUTH_TOKEN_FILE=/app/credentials/token.json
GOOGLE_OAUTH_CLIENT_JSON=<из .env, целиком JSON одной строкой>
GOOGLE_OAUTH_TOKEN_JSON=<из .env, целиком JSON одной строкой>
```

Дальше импортировать всё одной командой:

```bash
fly secrets import deploy-fly.env
```

После импорта файл `deploy-fly.env` можно удалить.

### Альтернатива — service account через base64
Если вместо OAuth используется сервисный аккаунт, заложи ключ как base64
(entrypoint сам распакует его в файл):

```bash
fly secrets set GOOGLE_SERVICE_ACCOUNT_JSON_B64="$(base64 -w0 path/to/service_account.json)"
```

## 5) Деплой

```bash
fly deploy
```

## 6) Проверка

```bash
fly logs
```

В логах должно появиться что-то вроде `Application started`.
После этого можно писать боту в Telegram.

## Советы

- `min_machines_running = 1` уже стоит в `fly.toml` — машина не останавливается.
- Если процессы остановятся совсем, поднять вручную:
  ```bash
  fly scale count 1
  ```
- Токен Google (`GOOGLE_OAUTH_TOKEN_JSON`) протухает, но бот сам обновляет его
  по `refresh_token` и перезаписывает файл при сохранении.