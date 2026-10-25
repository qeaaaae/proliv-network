# Proliv Network

Собственный VPN-сервис: Remnawave панель + Telegram-бот + Mini App + лендинг.

## Состав репо

| Путь | Что это |
|---|---|
| `docker-compose.yml` | локальный стенд: панель, БД, redis, subscription-page, лендинг |
| `proliv.env` | локальные секреты (в гит не коммитить) |
| `proliv.env.example` | шаблон env |
| `landing/` | Nuxt 4 лендинг в стиле ranteis.eu |
| `infra/` | скрипты и конфиги для VPS (deploy, caddy, node, bot) |
| `SPEC.md` | спецификация проекта |

## Локальный запуск

```powershell
# панель + бд + redis (порты 3000 панель/API, 3001 метрики, 6767 postgres)
docker compose --env-file proliv.env up -d

# + страница подписки на :3010 (нужен SUBPAGE_API_TOKEN из панели)
docker compose --env-file proliv.env --profile subpage up -d

# + лендинг на http://localhost:8080 (собирается из landing/)
docker compose --env-file proliv.env --profile site up -d --build

# + dev-прокси для панели (remnawave требует HTTPS через reverse proxy)
# панель: http://localhost:3443, страница подписки: http://localhost:3444
docker compose --env-file proliv.env --profile dev --profile site up -d
```

## Первый вход в панель

1. `docker compose --env-file proliv.env --profile dev up -d`
2. Панель: http://localhost:3443 - первый заход предложит создать superadmin
3. Settings -> API Tokens -> токен -> вписать в `SUBPAGE_API_TOKEN` в proliv.env
4. `docker compose --env-file proliv.env --profile subpage --profile dev up -d` - страница подписки на http://localhost:3444

## Telegram-бот

Форк и конфиги: `infra/bot.md`. Запуск:
`docker compose --env-file infra/tg-shop.env -f docker-compose.yml -f infra/tg-shop.compose.yml up -d`

Лендинг локально без докера:

```powershell
cd landing
npm install
npm run dev   # http://localhost:3000
```

## Деплой на VPS

## Деплой на VPS

См. `infra/vps-setup.md` - скрипт `infra/deploy-vps.sh` ставит Docker, генерит секреты, поднимает стек + Caddy с HTTPS.
