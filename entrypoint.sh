#!/bin/sh
# Скрипт выполняется перед запуском бота.
# Позволяет передать Google-ключ (service account) как base64 секрет,
# если в проекте не используется OAuth через env.

set -e

if [ -n "$GOOGLE_SERVICE_ACCOUNT_JSON_B64" ]; then
  # Декодируем JSON-ключ и подкладываем его как файл для Google API.
  echo "$GOOGLE_SERVICE_ACCOUNT_JSON_B64" | base64 -d > /app/service_account.json
  export GOOGLE_SERVICE_ACCOUNT_FILE=/app/service_account.json
fi

# Передаём управление процессу бота (python -m bot.main).
exec "$@"