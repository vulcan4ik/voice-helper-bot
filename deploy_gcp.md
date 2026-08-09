# Деплой на VM (Google Cloud) через Docker Compose

Бот работает через polling и сам ходит наружу (Telegram, Deepgram, Google Drive),
поэтому открытых портов не требуется — достаточно SSH. Машина не «засыпает»,
`restart: unless-stopped` сам поднимает бота после перезагрузки VM и при падениях.

Подготовленные файлы: `Dockerfile`, `entrypoint.sh`, `docker-compose.yml`, `.dockerignore`.

## 1) Зайти на VM

```bash
gcloud compute ssh <ИМЯ-ИНСТАНСА> --zone <ЗОНА>
```

## 2) Установить Docker и Compose plugin

Для Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-compose-plugin
sudo usermod -aG docker $USER
```

Выйди и зайди заново, чтобы подхватилось членство в группе `docker`.

## 3) Клонировать репозиторий

```bash
git clone https://github.com/vulcan4ik/voice-helper-bot.git
cd voice-helper-bot
```

## 4) Создать `.env`

Возьми из своего локального `.env`, но исправь пути Google-файлов на пути внутри контейнера:

```
BOT_TOKEN=<из локального .env>
ADMIN_ID=<из локального .env>
DEEPGRAM_API_KEY=<из локального .env>
GOOGLE_DRIVE_PARENT_ID=<из локального .env>
GOOGLE_OAUTH_CLIENT_FILE=/app/credentials/client_secret.json
GOOGLE_OAUTH_TOKEN_FILE=/app/credentials/token.json
GOOGLE_OAUTH_CLIENT_JSON=<из локального .env, целиком одной строкой>
GOOGLE_OAUTH_TOKEN_JSON=<из локального .env, целиком одной строкой>
```

Создать файл:

```bash
nano .env   # вставить строки выше и сохранить
```

Секреты не коммитятся (`.env` в `.gitignore` и `.dockerignore`).

## 5) Запустить бота

```bash
docker compose up -d --build
docker compose logs -f
```

В логах должно появиться `Application started`. После этого можно писать боту в Telegram.

## 6) Обновление бота

```bash
git pull
docker compose up -d --build
```

## 7) Перезагрузка VM

`restart: unless-stopped` поднимет контейнер автоматически.

## Проверка состояния

```bash
docker compose ps
docker compose logs -f
```