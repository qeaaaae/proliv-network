# TG-бот продаж: выбор форка и подключение к compose

> Ресёрч: 2026-10-25 (Jolymmiels), пересмотрено 2026-10-26 - выбран **форк minishop** как база под кастомизацию. Оригинал `machka-pasla/remnawave-tg-shop` (позже `kavore/remnawave-tg-shop`) архивирован; последняя проверенная им версия панели - Remnawave 2.6.4.

## Выбранный форк

**3252a8/remnawave-minishop** - переработанный форк kavore/remnawave-tg-shop, завендорен в `shop/` через `git subtree` (squash @ `c109364` = v3.8.3, 2026-10-23).

- Репо: https://gitlab.com/3252a8/remnawave-minishop (зеркало: github.com/3252a8/remnawave-minishop)
- Лицензия: **MIT** (чистая, без Commons Clause)
- Стек: Python 3.12, aiogram 3, aiohttp, SQLAlchemy 2 async, asyncpg, Pydantic, PostgreSQL 17, Redis 7, Svelte 5 (webapp)
- Образы: `3252a8/remnawave-minishop-{backend,worker,frontend}` на Docker Hub (`dev`, `candidate-<sha>`, релизные теги); для разработки собираем из `shop/` (`--build`)

### Почему именно он

| Критерий | minishop | Bedolaga | Jolymmiels | VAQYBIN/tg-shop |
|---|---|---|---|---|
| Стек | **Python** (aiogram3/aiohttp/SA async) | Python 3.14 | Go | Python/FastAPI+React |
| Лицензия | **MIT** | MIT + **Commons Clause** (риск для коммерции) | AGPL-3.0 | MIT |
| Remnawave v3 | **да, сертифицировано 3.0.0-3.4.5** (`remnawave_support.json`, live coverage) | да, 3.0.0+ | да (5.x ↔ 3.4.x) | да, 3.2.1-3.4.3 |
| YooKassa | да, webhook | да, webhook | да, webhook | да |
| Провайдеры | 14 (YooKassa, Stars, CryptoPay, Tribute, CloudPayments, Wata, Platega, FreeKassa...) | 18-28 | 5 | ~6 |
| Из нашего SPEC | докупки трафика/устройств, рефералка, промокоды-триал, Mini App с initData+email, инструкции подключения, статус серверов (Kuma), тарифный каталог, HWID-пакеты | всё + баланс, NaloGO | 4 фикс-тарифа, без докупок | базовый шоп |
| Активность | релиз v3.8.3 за 3 дня до форка, коммиты еженедельно | 9.4k коммитов, активен | релизы до сен 2026 | мелкий |

Причины отказа от альтернатив:
- **Bedolaga**: Commons Clause - продажа VPN через него юридически серая зона; 28 провайдеров и свой React-кабинет - лишний багаж (наш кабинет = `cabinet/`).
- **Jolymmiels**: Go + AGPL (модификации надо открывать), нет докупок - только деплой «как есть». Оставлен запасным: `infra/tg-shop.compose.yml`.
- **VAQYBIN**: 13 звёзд, качество непроверено.
- **kavore-оригинал**: мёртв, панель <= 2.6.4.

## Структура shop/

- `backend/` - бот + webhook-сервер + WebApp API (один код, `backend/main_*.py` входные точки)
- `frontend/` - Svelte 5 Mini App (юзерский ЛК + веб-админка)
- `deploy/docker/Dockerfile` - multi-stage: `backend`, `worker`, `frontend`
- `deploy/dev/` - сиды и стенды панели по версиям (3.0.0-3.4.5), `docker-compose.remnawave-dev.yml` - их собственный dev-stend с панелью (нам не нужен, своя панель в корневом compose)
- `migrations/`, `tests/`, `docs/`, `locales/ru.json|en.json`

### Правила разработки в shop/ (upstream, обязательны)

`shop/CONTRIBUTING.md` + `shop/AGENTS.md`/`CLAUDE.md`: mypy строго зелёный (никаких `type: ignore`/`any` в first-party), миграции БД append-only, `{"ok": ...}` envelope - wire contract, тексты UI/бота - только через `locales/ru.json`+`en.json`, фронт - Svelte runes + TS only, гейты перед пушем: `pytest`, `ruff`, `mypy`, `npm run check`. Conventional Commits, без Co-Authored-By.

## Запуск локально

```powershell
cp infra\minishop.env.example shop\.env   # один раз, заполнить секреты
docker compose up -d                       # поднять нашу панель (корневой compose)
docker compose -f shop\docker-compose.yml -f infra\minishop.compose.yml up -d --build
```

- Overlay `infra/minishop.compose.yml` добавляет `backend`/`worker`/`migrate`/`bot` в нашу сеть `remnawave-network` (external) -> панель доступна как `http://remnawave:3000/api`.
- Порты: **8085** backend (webhooks + `/healthz`), **8086** webapp/админка, **8088** bot (только при поднятом профиле). Сдвинуты с дефолтов 8080/8082 - они заняты landing/cabinet.
- Postgres/Redis minishop'а - свои контейнеры (`remnawave-minishop-postgres/-redis`), с панельной БД не пересекаются.
- Миграции БД применяет сервис `migrate` при старте.
- Сервис `bot` за compose-профилем `bot`: обычный `up -d` его **не поднимает**. См. топологию ниже.

## Что требует публичного домена

- **Telegram** - только webhook (`WEBHOOK_BASE_URL` + setWebhook). Polling-режима нет. Для локалки: `TELEGRAM_ENABLED=False` (браузерный режим, бот не ходит в TG API) или туннель -> `127.0.0.1:8088` (порт сервиса `bot`; пример rathole есть в `shop/deploy/examples/rathole/`).
- **Mini App-кнопки бота** - Telegram разрешает WebApp-кнопки только на HTTPS. URL берётся из `PUBLIC_APP_URL`/`SUBSCRIPTION_MINI_APP_URL` -> для локалки тоже нужен туннель, уже на кабинет `127.0.0.1:8082`. Иначе `/start` отправляет приветствие, а меню падает с `inline keyboard button Web App URL ... Only HTTPS links are allowed`.
- **YooKassa** - вебхук `WEBHOOK_BASE_URL/webhook/yookassa...`, в проде нужен `bot.<domain>` -> backend:8080 (внутри контейнера).
- **Вебхуки панели** -> `WEBHOOK_BASE_URL/webhook/panel`, секрет `PANEL_WEBHOOK_SECRET` одинаковый в панели и `.env`.
- **Telegram Stars** - без домена (оплата внутри Telegram).
- Связка панель->бот локально: панель в `remnawave-network` может слать вебхуки в `http://remnawave-minishop-backend:8080/webhook/panel` (для теста панельных событий, секрет из .env).

### Локальные dev-туннели (cloudflared)

Для живого бота на локалке нужны **два** quick-туннеля (`infra/tools/cloudflared.exe`, скачивается скриптом):

| Туннель | Локальный порт | Куда пишется URL в `shop/.env` |
|---|---|---|
| bot webhook | `127.0.0.1:8088` (сервис `bot` -> :8080) | `WEBHOOK_BASE_URL` (Telegram шлёт на `.../tg/webhook`) |
| cabinet | `127.0.0.1:8082` (наш ЛК, Nuxt) | `PUBLIC_APP_URL` + `SUBSCRIPTION_MINI_APP_URL` |

Запуск обоих + авто-патч `shop/.env`:

```powershell
powershell -ExecutionPolicy Bypass -File infra\tunnels.ps1         # поднять
powershell -ExecutionPolicy Bypass -File infra\tunnels.ps1 -Stop   # убить
```

Скрипт поднимает два `cloudflared tunnel --protocol http2` (QUIC/UDP 7844 у нас блокируется - без `http2` туннель не коннектится), выдирает `*.trycloudflare.com` URL из логов и пишет три ключа в `shop/.env`.

Ловушки:
- **URL эфемерные**: каждый прогон туннеля = новый домен -> каждый раз после `tunnels.ps1` пересоздавать сервисы: `docker compose -f shop/docker-compose.yml -f infra/minishop.compose.yml --env-file shop/.env up -d bot backend`. `docker compose restart` **не перечитывает env_file** - старый URL останется в контейнере и вебхук сломается.
- trycloudflare - только для дева, без гарантий; прод = именованный туннель или свой домен + edge-прокси.
- Логи туннелей: `%TEMP%\proliv-tunnels\*.err.log`.

## Топология: бот отдельно, бэкенд ЛК отдельно

Целевая схема (требование): **бот - отдельный сервис, бэкенд ЛК - отдельный и покрывает всю доменную логику** (платежи, юзеры, подписки, remnawave-синк, рефералка, промокоды). Наш `cabinet/` (Nuxt) ходит в бэкенд по WebApp API.

Важно про upstream-код (`shop/backend/bot/main_bot.py`, `web_server.py`):

- Точек входа три: `main_backend.py` (web+TG), `main_worker.py`, `main_migrate.py`. `bot/main_bot.py` - не скрипт, а модуль с `run_bot()`/`run_web_only()`; polling-режима нет вообще, только webhook.
- `TELEGRAM_ENABLED=False` -> `run_web_only()`: aiohttp :8080 (вебхуки провайдеров/панели) + :8081 (WebApp API), доменные сервисы, `bot=None` - BOT_TOKEN не нужен вообще.
- `TELEGRAM_ENABLED=True` -> `run_bot()`: тот же aiohttp :8080/:8081 + aiogram-диспетчер, роут `POST /tg/webhook` и `setWebhook(WEBHOOK_BASE_URL + /tg/webhook)` при старте. «Бот без HTTP» не существует - процесс всегда полный.
- Вебхуки платёжных провайдеров и панели - тонкие приёмники: кладут событие в Redis-очередь, разгребает её `worker`. Поэтому несколько HTTP-инстансов безопасны: событие обработается один раз независимо от того, кто его принял.
- `BOT_TOKEN` нужен не только боту: `/api/auth/token` (initData / Telegram Login Widget) гейтится `TELEGRAM_ENABLED and BOT_TOKEN` (HMAC-проверка локальная, но флаг обязателен), и TG-уведомления шлются Bot-клиентом. Значит в проде `TELEGRAM_ENABLED=True` нужен backend'у и worker'у тоже - иначе TG-логин в ЛК и уведомления мертвы.

Как это ложится на сервисы compose:

| Сервис | Entry | Роль |
|---|---|---|
| `backend` | `plugin_launcher.py backend` -> `main_backend.py` | WebApp API :8081 + вебхуки провайдеров/панели :8080; в проде TELEGRAM_ENABLED=True ради auth и исходящих TG-вызовов, но апдейты на него не роутим |
| `bot` | тот же образ, `command: python backend/main_backend.py` | TG-диспетчер + приём апдейтов на :8080 (`/tg/webhook`); WEBAPP_ENABLED=false |
| `worker` | `main_worker.py` | фоновые задачи + consumer Redis-очереди вебхуков (тарифы, уведомления, синк, рассылки) |
| `migrate` | `main_migrate.py` | миграции БД |
| `frontend` | nginx | штатный webapp (MVP ЛК + админка) |

Реализовано в `infra/minishop.compose.yml` (сток, **без правок кода**):

- `bot` - второй инстанс backend-образа за профилем `bot`: `TELEGRAM_ENABLED=True`, `WEBAPP_ENABLED=false`, общие PG+Redis+`shop-data`. Штатный `plugin_launcher` обойдён (`command:` на `main_backend.py`): два лаунчера роли "backend" конкурировали бы за общий plugin-store (`observations["backend"]`, двойной запуск миграций при смене поколения плагинов). Плагины при старте грузятся из общего store, но **после установки/обновления плагина в админке нужен `docker compose ... restart bot`** - авто-перезапуска по смене поколения у него нет.
- Разделение трафика - на edge: публичный `WEBHOOK_BASE_URL` один на все инстансы, прокси/девпрокси направляет `POST /tg/webhook` -> `remnawave-minishop-bot:8080`, всё остальное (`/webhook/*`, `/api/*`, `/healthz`) -> `remnawave-minishop-backend:8080`. Оба инстанса вызывают `setWebhook` с одним URL - идемпотентно; даже если апдейт случайно придёт на backend, его диспетчер обработает корректно (код идентичен, БД общая).
- Платёжные `url_callback` строятся из `WEBHOOK_BASE_URL` инстанса, создавшего инвойс -> с единым base URL и path-routing'ом они всегда попадают на backend.

Команды:

```powershell
# Dev (как сейчас): backend web-only, worker, frontend. Бота нет - TG-логин
# в webapp недоступен (initData-гейт), локально входим по email.
docker compose -f shop\docker-compose.yml -f infra\minishop.compose.yml --env-file shop\.env up -d --build

# Поднять и bot (нужны реальные BOT_TOKEN + WEBHOOK_BASE_URL в shop/.env):
docker compose -f shop\docker-compose.yml -f infra\minishop.compose.yml --env-file shop\.env --profile bot up -d --build

# Только bot к уже работающему стеку:
docker compose -f shop\docker-compose.yml -f infra\minishop.compose.yml --env-file shop\.env up -d bot
```

Прод-включение (когда появится реальный токен):

1. `shop/.env`: `TELEGRAM_ENABLED=True`, `BOT_TOKEN=<реальный>`, `WEBHOOK_BASE_URL=https://<домен>`, `WEBHOOK_SECRET_TOKEN`, `WEBAPP_SESSION_SECRET`.
2. В `infra/minishop.compose.yml` убрать dev-блок environment у `backend` (TELEGRAM_ENABLED=False, WEBAPP_SESSION_SECRET, APP_RUNTIME_MODE=dev, QA_AUTH_ENABLED, EMAIL_LOGIN_ENABLED) - см. комментарий в файле.
3. Edge: `POST /tg/webhook` -> `bot:8080`, остальное -> `backend:8080`.
4. `up -d --profile bot` (или просто `up -d bot` на живом стеке).

- **Полный сплит** (при кастомизации): вынос TG-диспетчера в отдельный процесс без HTTP - потребовал бы код-патч в `run_bot()`/`build_and_start_web_app()` (флаг типа `WEB_SERVER_ENABLED`), дороже и усложняет upstream merge. Текущего разделения на уровне сервисов + edge-routing достаточно.

Пока `TELEGRAM_ENABLED=False` и токена нет - живёт один `backend` в web-only режиме, `bot` не поднимается (профиль).

## Владелец/админка

- `BOOTSTRAP_OWNER_TELEGRAM_ID` или `BOOTSTRAP_OWNER_EMAIL` -> первый владелец при первом входе в webapp. Дальше роли в админке (Admin -> Users).
- Админка живёт в webapp: `http://127.0.0.1:8086` -> Admin. Тарифы/провайдеры/тексты - там, без рестарта.

## Тарифы и SPEC-маппинг

- Тарифный каталог - JSON в админке (Admin -> System -> Tariffs): наш тариф 179 ₽/мес, 3 устройства, 300 ГБ/мес с переносом остатка (`MONTH_ROLLING` + `traffic_rollover`); докупки +100 ГБ/49 ₽, +500 ГБ/149 ₽, +1 устройство/29 ₽ - нативные topup-пакеты и HWID-пакеты.
- Триал только по промокоду/рефералке: промокоды и реферальные ссылки поддерживаются нативно; реферальные проценты (15% рефереру / 20% другу) настраиваются в админке.
- Фискализация самозанятого: `lknpd_*` сервисы (lknpd.nalog.ru, Мой Налог) - аналог MOYNALOG у Jolymmiels.
- Mini App: штатный Svelte-webapp minishop'а как MVP; свой `cabinet/` (Nuxt) - как замена лицевой части позже, бэкенд minishop'а при этом остаётся API-слоем (его WebApp API + initData-авторизация).

## Upstream-синхронизация

```powershell
git subtree pull --prefix=shop https://gitlab.com/3252a8/remnawave-minishop.git main --squash -m "vendor: bump remnawave-minishop"
```

Конфликты с нашей кастомизацией разруливаются как обычный merge. Перед pull проверить совместимость панели: `shop/backend/bot/services/remnawave_support.json` (certified_versions) vs наш `remnawave/backend:3` тег.

## Запасной вариант (Jolymmiels)

Если minishop не взлетит - `infra/tg-shop.compose.yml` + `infra/tg-shop.env.example` деплоят готовый Go-бот `ghcr.io/jolymmiels/remnawave-telegram-shop-bot:5.1.0` (long polling, YooKassa-webhook, MoyNalog-чеки). Не форкаем: AGPL + нет докупок.

## Ссылки

- Форк (upstream): https://gitlab.com/3252a8/remnawave-minishop
- Доки upstream: `shop/docs/` (env-справочник: `shop/docs/configuration/env-vars.md`)
- Матрица версий панели: `shop/backend/bot/services/remnawave_support.json`
- Запасной бот: https://github.com/Jolymmiels/remnawave-telegram-shop, https://docs.rwp.rw/ru/
