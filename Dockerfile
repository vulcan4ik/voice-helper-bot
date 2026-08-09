# Лёгкий образ Python 3.11 для деплоя на Fly.io.
FROM python:3.11-slim

# Рабочая директория внутри контейнера.
WORKDIR /app

# Сначала ставим зависимости (слой кэшируется при изменении только кода).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальной код проекта (секреты исключены через .dockerignore).
COPY . .

# Entrypoint выполняется перед запуском бота (настраивает Google-ключи при необходимости).
ENTRYPOINT ["sh", "/app/entrypoint.sh"]

# Команда по умолчанию: запуск бота.
CMD ["python", "-m", "bot.main"]