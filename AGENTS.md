# AGENTS.md - ProlivVPN

Правила работы агента в этом репозитории. Спека продукта - `SPEC.md`, архитектура бота - `infra/bot.md`.

## Жёсткие правила

1. **`.env*` НЕ ТРОГАТЬ САМОМУ.** Никогда не писать и не править `.env`, `.env.local`, `.env.<anything>` (`proliv.env`, `shop/.env` и т.д.) ни через файловые инструменты, ни через shell. Вместо этого:
   - дать пользователю готовую команду/строки для вставки;
   - явно написать, куда её вводить (файл, терминал, compose-команда пересоздания);
   - `.env.example` / `*.env.example` править можно.
2. **Секреты - только в `.env`, никогда в git** и не выводить значения в лог/чат (маскировать при печати).
3. **`shop/` - vendored fork** `3252a8/remnawave-minishop` (git subtree, upstream pull через `git subtree pull --prefix=shop`). Правила кода внутри: `shop/AGENTS.md` + `shop/CONTRIBUTING.md` - читать перед правками там. Не править сгенерированные файлы (`openapi.json`, `events.md`, `openapi.generated.ts`, settings manifest), миграции append-only.
4. Не коммитить/не пушить без явной команды. Не стирать и не перезаписывать незакоммиченные изменения пользователя.
5. Чужие процессы не убивать (занятые порты - обходить другим портом, спрашивать, если критично).
6. **ВСЕ ПРАВКИ - СРАЗУ НА СЕРВЕР.** Любую правку кода/конфига, которую просит пользователь, применять на проде (`proliv-main`, `/opt/proliv`) в той же сессии без отдельной команды «деплой»: scp файлов -> пересборка/пересоздание нужных контейнеров -> проверка health/логов. Локальная правка без выката = задача НЕ сделана. Перед заливкой сверять файл с серверной копией (на сервере свой working tree - не затереть чужие правки). Compose только из `/opt/proliv`: корневой стек строго `--env-file proliv.env` (НИКОГДА `shop/.env` - там нет `NUXT_*`-ключей, кабинет пересоздастся с пустым env и Telegram-логин умрёт 503), minishop - `-f shop/docker-compose.yml -f infra/minishop.compose.yml -f infra/minishop.prod.compose.yml --env-file shop/.env --profile bot`. Данные в volumes (`/app/data/tariffs.json`, `locales-overrides.json`) правятся внутри контейнера отдельно от сидов в репо.
7. **НА СЕРВЕРЕ - ТОЛЬКО PROD-РЕЖИМ. НИКАКИХ ТЕСТОВ, НИКАКОГО DEV.** На `proliv-main` и всех нодах строго запрещено:
   - запускать minishop БЕЗ `infra/minishop.prod.compose.yml` - в `infra/minishop.compose.yml` зашиты dev-дефолты (`APP_RUNTIME_MODE=dev`, `QA_AUTH_ENABLED=True`, `EMAIL_LOGIN_ENABLED=True`, dev-секрет сессий), и без prod-оверлея `PANEL_WRITE_MODE=auto` резолвится в **dry-run**: записи юзеров в панель молча глушатся -> подписки слетают при следующей синхронизации (уже случилось 2026-10-28);
   - выставлять `APP_RUNTIME_MODE=dev` / `QA_AUTH_ENABLED=True` / `EMAIL_LOGIN_ENABLED=True` / `PANEL_WRITE_MODE=dry-run` / dev-секреты (`proliv-local-dev-secret`) в ЛЮБЫХ env/оверлеях/аргументах прода - ни в бэке, ни в боте, ни в воркере;
   - гонять тесты на проде вообще: никаких `pytest`/`vitest`/`npm test`/e2e-скриптов ни на бэке, ни на фронте (кабинет, лендинг, Mini App), ни в боте. Проверки - только локально или в CI; на сервере допустимы только `docker ps`/логи/health-пробы и read-only SQL (мутации - отдельно по правилам поддержки).
   - Любая проверка «прод работает» - только наблюдением (логи, healthcheck, реальный запрос), не исполнением тестового кода на проде.

## Карта репозитория

| Путь | Что это |
|---|---|
| `landing/` | Nuxt 3 SPA, статик-сайт (nginx), порт 8080 |
| `cabinet/` | Nuxt 4 SSR (`ssr:false`), личный кабинет + BFF в `server/`, порт 8082 |
| `shop/` | vendored minishop: Python 3.12, aiogram 3, aiohttp, SQLAlchemy async, PG, Redis, Svelte |
| `infra/` | compose-оверлеи, env-шаблоны, `bot.md` |
| `docker-compose.yml` | панель remnawave + db + redis + devproxy + landing + cabinet |
| `proliv.env(.example)` | env корневого compose |
| `infra/minishop.*` | overlay + env-шаблон для shop |

## Архитектура рантайма

- `remnawave` панель: `http://remnawave:3000` в `remnawave-network`, метрики/health на 3001.
- `remnawave-minishop-backend`: API ЛК (webapp) на `:8081`, вебхуки/HTTP на `:8080`; в `remnawave-network` через `infra/minishop.compose.yml`.
- `proliv-cabinet`: BFF (`cabinet/server/utils/backend.ts`) ходит в `NUXT_SHOP_API_URL` (по сети `http://remnawave-minishop-backend:8081`). Сессия `proliv_session` хранит `apiToken`+`apiCsrf` minishop; мутации идут с `X-CSRF-Token`.
- Auth-мост: `cabinet` принимает `initData` (Mini App) или widget-поля -> `POST {shop}/api/auth/token` -> Bearer.
- Минишоп ходит в панель по `PANEL_API_URL`/`PANEL_API_KEY` (shop/.env).

## Команды

```powershell
# Панель + лендинг + кабинет (корень)
docker compose --env-file proliv.env --profile app up -d cabinet
docker compose --env-file proliv.env --profile site up -d landing

# Minishop (отдельный compose-проект; порты хоста: backend 8085*, frontend 8086)
docker compose -f shop/docker-compose.yml -f infra/minishop.compose.yml --env-file shop/.env up -d --build

# *Если порт занят локальным процессом - переопределить только на запуск:
$env:WEB_SERVER_PORT='8087'; docker compose -f shop/docker-compose.yml -f infra/minishop.compose.yml --env-file shop/.env up -d backend frontend

# Кабинет
cd cabinet; npx nuxi prepare; npx nuxi typecheck; npm run build

# Minishop quality gates (перед коммитом в shop/)
cd shop; pytest; ruff check backend; mypy backend; cd frontend; npm run check
```

## Boundaries

- **Always:** typecheck кабинета после правок `cabinet/server`; проверять `docker compose config` перед подъёмом; тестировать эндпоинты кабинета через реальный запрос с кукой, а не «должно работать».
- **Ask first:** правки внутри `shop/` (форк - каждое изменение усложняет upstream-merge); новые зависимости; правки compose-сетей/портов; любые деструктивные действия с docker volumes/БД.
- **Never:** писать в `.env*`; коммитить секреты; тянуть `latest`-теги образов в прод-конфиги; включать деструктивные SQL/миграции без аппрува; `git push` без явной команды.

## Типичные ловушки

- `shop/` собирается только с `shop/.git` (gitfile `gitdir: ../.git` - нужен для bind-mount в Dockerfile; git его не трекает). Build-args `REMNAWAVE_MINISHOP_BUILD_*` в `infra/minishop.compose.yml` задают версию без git-истории.
- `TELEGRAM_ENABLED=False` выключает и `/api/auth/token` (initData-auth) - для webapp нужен `True` + валидный `BOT_TOKEN` (aiogram валидирует при старте, фейк-токен = crash-loop).
- `APP_RUNTIME_MODE=dev` (стоит в `infra/minishop.compose.yml`) превращает `PANEL_WRITE_MODE=auto` в **dry-run** - юзеры в панели не создадутся. На проде ЗАПРЕЩЕНО (правило 7): поднимать minishop только с prod-оверлеем `infra/minishop.prod.compose.yml`, dev-флаги на сервере не выставлять никогда.
- Vendored-патч: `shop/backend/bot/payment_providers/yookassa/webhook.py` - `app_required("bot")` -> `app_optional` (иначе вебхук ЮKassa падал 500 при выключенном TG). При `git subtree pull` следить, чтобы upstream не затёр; если затёр - вернуть 1-строчный патч.
- Vendored-патч: `shop/backend/bot/app/web/webapp/csrf_origin.py` - `_allowed_browser_origins` добавляет origin `WEBAPP_ADMIN_URL` в CSRF-allowlist (upstream разрешал только `SUBSCRIPTION_MINI_APP_URL` -> все POST с admin-домена умирали 403 csrf_failed, включая initData-auth кнопок из бота). При `git subtree pull` следить, чтобы upstream не затёр.
- Vendored-патч: `shop/backend/bot/services/subscription_service_impl/devices.py` - `_quote_hwid_package_price` капит `proration_ratio` на 1.0 (upstream умножал цену пакета на ВСЕ оставшиеся биллинг-периоды подписки: у выданной вручную длинной подписки +1 устройство стоило десятки тысяч). Теперь докупка стоит макс. один период; внутри периода пропорция дней сохраняется. Тесты `test_hwid_device_topup.py` обновлены (ratio 13.0/1.5 -> 1.0). При `git subtree pull` следить, чтобы upstream не затёр.
- Vendored-патч (админка в боте вместо webapp): `shop/backend/bot/handlers/admin/support_admin.py` (новый) - тикеты прямо в боте: `admin_ticket:<id>` view, `admin_ticket_reply:<id>` FSM-ответ (`AdminStates.waiting_for_support_reply`), `admin_ticket_status:<id>:(open|resolved|closed)`, диплинк `/start admin_ticket_<id>` в `start_flow.py`. `notification_support._support_keyboard`: в ЛС админов - callback-кнопки вместо web_app, в лог-канал - `?start=admin_ticket_<id>` диплинк (юзерская клавиатура не тронута). `auth_common._admin_panel_only_request` + `assets.py` bootstrap `adminPanelOnly` + `AppModeContent.svelte` заглушка "wa_admin_open_in_telegram" вместо AuthScreen на admin-origin. `infra/Caddyfile`: на admin.* whitelist `/admin* /api/* /subscription_webapp* /webapp-* /provider-logos/* /fonts/* /favicon.ico /apple-touch-icon* /icon-* /robots.txt`, остальное 404. Локали `admin_ticket_*` в ru/en. Тесты: `tests/unit/test_support_notifications.py`, `test_security.py`.
- Отдельный `bot`-сервис в `infra/minishop.compose.yml` за профилем `bot` (`--profile bot`): backend=web-only, bot=TG+`/tg/webhook` (:8080). Прод-роутинг: `/tg/webhook` -> bot:8080, остальное -> backend:8080.
- YooKassa: method-id `yookassa`, цены в рублях-строками, вебхук `POST {WEBHOOK_BASE_URL}/webhook/yookassa` (IP-вайтлист без подписи), тарифы - `data/tariffs.json`/админка. Гайд: `infra/yookassa.md`. Панель: `infra/panel-setup.md`. Брендинг: `infra/branding.md` + `infra/seed/`.
- Non-TG логин локально: email-auth. Включается связкой `APP_RUNTIME_MODE=dev` + `QA_AUTH_ENABLED=True` + `EMAIL_LOGIN_ENABLED=True` (в `infra/minishop.compose.yml`). Юзеру в БД нужны `email`, `email_verified_at`, `password_hash` (формат `pbkdf2_sha256$260000$b64salt$b64digest`, `hashlib.pbkdf2_hmac`). Тестовый юзер: `dev@proliv.dev` / `admin12345` (user_id 1000000000000, telegram_id 880994961). `cabinet` dev-login admin/admin сам идёт в `/api/auth/email/password`.
- Minishop виснет ~20с на запросах с `Accept: application/json` + `Accept-Encoding: gzip/br` (путь сжатия). BFF всегда шлёт `Accept-Encoding: identity` - не убирать.
- POST/PUT в WebApp API без JSON-тела upstream отклоняет (`invalid_payload`) - всегда слать `body: {}` минимум.
- Фича-флаги minishop (404 `*_disabled`): `MY_DEVICES_SECTION_ENABLED`, `SUBSCRIPTION_REISSUE_ENABLED` - включены в dev-overlay; триал выключен по спеке.
- `curl` в PowerShell = `Invoke-WebRequest` (другие флаги); использовать `curl.exe` или `iwr`.
- `Get-Content`/`Select-String` не читают пути с `[]` - через read-инструмент или `-LiteralPath`.
- Кириллица в консоли = mojibake - читать файлы инструментами, не грепать вывод.
- **`docker compose restart` не перечитывает env_file** - после правки `shop/.env` всегда `up -d <svc>` (пересоздание), иначе контейнер живёт со старым env.
- Локальному окружению нужны **три** туннеля: `8088` -> `WEBHOOK_BASE_URL` (TG webhook), `8082` -> `PUBLIC_APP_URL`/`SUBSCRIPTION_MINI_APP_URL` (Mini App, только HTTPS) и `8080` -> лендинг (`REFERRAL_INFO_URL` = `<landing-tunnel>/offer#referral`). Поднятие + авто-патч `shop/.env`: `infra\tunnels.ps1` (cloudflared, `--protocol http2` - QUIC у нас блокируется; URL эфемерные, после каждого запуска `up -d bot backend`). Детали: `infra/bot.md` -> "Локальные dev-туннели".
- **`parse_mode=None` явно = выключить дефолтный HTML** (aiogram 3.7+): симптом - сырые `<b>`/`<code>`/`<tg-emoji>` в подписях карточек. В общих хелперах пробрасывать kwarg только когда он задан - см. `_parse_kwargs` в `shop/backend/bot/handlers/user/menu_card.py`.
- Карточки бота: `send_card`/`render_card` (`bot/handlers/user/menu_card.py`) - одно фото-сообщение, caption/кнопки по стейту; фото `/app/data/branding/welcome.png`, caption <= 1000 символов, иначе фолбэк на текст.
- Кастомные эмодзи в текстах: `<tg-emoji emoji-id="ID">юникод-фолбэк</tg-emoji>`; юникод->теги конвертер `infra/replace_locale_emojis.py` (карта `infra/TgAndroidIcons.txt`, алиасы внутри скрипта; пропускает `*_button` и admin_/wa_/webapp_-ключи). `CustomEmojiFallbackMiddleware` сам срезает теги при отказе API. На кнопках - `icon_custom_emoji_id` через `TELEGRAM_MENU_APPEARANCE_JSON`.
- `app_setting_overrides` применяет только ключи с `SettingField` в манифесте - без поля ключ молча скипается (см. `Applied N overrides` в логах). Новые настройки: поле в `admin_settings_manifest_fields.py` + регенерация `frontend/src/lib/webapp/settingsManifest.generated.json` (sync-тесты). Значения в БД - JSON-encoded (`'"значение"'`).
- Новые кнопки главного меню бота: добавить id в `MENU_APPEARANCE_ENTRIES`, иначе `TELEGRAM_MENU_APPEARANCE_JSON` override падает с 'unknown system menu button'.
- `psql -c` через PowerShell ломает кавычки - SQL писать в файл и `Get-Content f.sql | docker exec -i remnawave-minishop-postgres psql -U remnawave_minishop -d remnawave_minishop`.
- Рефералка-шаринг: кнопка 'Пригласить друга' = URL `https://t.me/share/url?url=<ref>&text=<intro>` (встроенный выбор чата, работает без BotFather /setinline; `switch_inline_query` требует включённый inline-режим).

## Прод-инфраструктура (развёрнута 2026-10-27)

- `proliv-main` (Швеция, `144.31.240.216`): VPS-0 - панель+лендинг+бот+ЛК. Стек в `/opt/proliv` (`docker-compose.yml`+`proliv.env` скопированы scp). Панель v3.4.7 + postgres:18.4 + valkey:9 + subpage v8.0.1 + caddy devproxy (:3443 панель, :3444 subpage - обязателен, иначе ProxyCheckMiddleware отклоняет plain-HTTP). **devproxy - постоянный сервис (не dev-профиль)**: `REMNAWAVE_PANEL_URL` у subpage = `http://proliv-devproxy:3443`, офиц. образ сам X-Forwarded-* не шлёт (без моста: GetSubscriptionInfo 404/сокет-дроп -> 502 на браузерных запросах). Minishop ходит в панель напрямую - свой клиент добавляет заголовки (`panel_api_core.py`, `remnawave_subscription_source.py`).
- `proliv-node-de` (Германия, `13.143.192.49`): `remnawave/node:3.4.3` в `/opt/remnanode` (network_mode host, NODE_PORT=2222, SECRET_KEY в `/opt/remnanode/.env`). UFW: 22+443 всем, 2222 только с 144.31.240.216.
- SSH: алиасы в `~/.ssh/config`, ключ `~/.ssh/proliv`; root по ключу + deploy(1000,sudo), парольный вход выключен.
- Панель-админ: `admin` (пароль в выдаче юзеру 2026-10-27, политика: 24+ симв A-Za-z0-9). Админка: `ssh -L 3443:localhost:3443 proliv-main` -> http://localhost:3443.
- **API-токен панели без UI**: вставить строку в `api_tokens`, затем JWT `{uuid:<uuid_строки>,username:null,role:'API'}` HS256 подписать `APP_SECRET` (секрет берётся из env, не из JWT_*-переменных). Рабочий токен: `/root/.panel-jwt` на main.
- **Архитектура ноды (remnawave 3.x)**: панель САМА коннектится к ноде на NODE_PORT (mTLS, TLS1.3) - на панели порты под ноды не открываются; SECRET_KEY = `GET /api/keygen` (без суффиксов). xray x25519 генерить только xray-бинарём.
- Контракты API панели: npm-пакет `@remnawave/backend-contract@<версия_панели>` - читаемые zod-схемы всех команд (routes.js + commands/*.command.js).
- ВНИМАНИЕ: `docker compose` на сервере гонять ТОЛЬКО из `/opt/proliv` с `--env-file proliv.env`; shell-env переменные перекрывают env-файл (так прокинут `SUBPAGE_API_TOKEN` в subpage без правки файла).
- **RU-DPI vs фрагментированный ClientHello**: hello >MSS рвётся на 2 сегмента -> DPI держит первый, второй до сервера не доходит -> `REALITY: processed invalid connection ... failed to read client hello` (ждёт ~10с -> рубит). Не использовать fp=`chrome`/`firefox` (PQ-ключи раздувают hello до 1.7-1.9KB). **Обновлено 2026-10-27 вечер:** Happ 5.8 игнорирует `fp` из vless-ссылок (шлёт свой hello 1539B с X25519MLKEM768 при любом fp в ссылке), а `safari` у него тоже с PQ. Рабочая схема: response rule `Happ/Incy (xray json)` (UA `^(happ|incy)` -> `XRAY_JSON`) + fp=`edge` на Reality-хостах - из JSON-конфига Happ fp применяет (подтверждено: UK/EE accepted). Диагностика размера hello: `/tmp/hs.sh` на ноде (`hello_size.sh` в корне репо) - печатает TLS record len и наличие PQ (`11ec`); >1283 = не влезет в сегмент при MSS 1300.
- **ipregion в /nodes**: на каждой ноде `infra/ipregion-node-install.sh` (скрипт vernette/ipregion в `/opt/ipregion`, systemd-таймер раз в 6ч -> `/opt/ipregion/last.json`). `infra/status-probe.py` забирает файл тем же SSH-пробом и кладёт `geo` в `status.json`, бот рендерит каждую ноду отдельной `<blockquote>` (`shop/backend/bot/handlers/admin/nodes_geo.py`). Ручной перезапуск проверки: `systemctl start ipregion.service` на ноде.
- REALITY-логи на ноде: `docker exec remnanode tail -f /var/log/xray/current`; паттерны: `server name mismatch` = старая ссылка/SNI, `failed to read client hello` = обрезанный/битый hello (DPI или проба), `authentication failed` = кривые креды, `accepted tcp:X >> DIRECT` = рабочая сессия.
- E2E-тест туннеля без клиента: контейнер `xray-client-test` на main (`docker exec remnawave sed`-шаблон + socks5:10808) - `curl --socks5-hostname 127.0.0.1:10808 ifconfig.co` должен отдать IP ноды.
- **Брендинг подписки (настроено 2026-10-27)**: `PATCH /api/subscription-settings` (uuid = `00000000-...` обязателен в теле). `customResponseHeaders`: `profile-title`/`announce` через `rwEncodeBase64:<текст>` (шаблоны per-user работают и в хедерах: `announce` = `🔔 Подписка: {{TELEGRAM_ID}}` + легенда `⚡` = YouTube без рекламы, `📱 LTE` = только моб. интернет; `⚡` ставить в remark хостов, где ipregion показывает `YouTube: RU`), `support-url`, `profile-web-page-url`, `announce-url`, `profile-update-interval`. `customRemarks` - только для стейтов (expired/limited/disabled/empty/HWID*), НЕ для инфо-строк.
- **Инфо-строки в списке серверов** = фейковые хосты `127.0.0.1:9` привязанные к инбаунду (НЕ используем - клиент сам рендерит дни/трафик из `subscription-userinfo`). Remark хоста шаблонизируется ПЕР-ЮЗЕРОМ: `{{DAYS_LEFT}}`, `{{TRAFFIC_USED}}`, `{{USERNAME}}` и др. **Конвенция имён серверов: `🇩🇪 Германия` (флаг + страна, БЕЗ префикса Proliv - решено юзером 2026-10-27).** Порядок: `POST /api/hosts/actions/reorder` телом `{"hosts":[{uuid,viewPosition}...]}`; удаление: `DELETE /api/hosts/{uuid}`.
- **LTE-хосты (VLESS+xhttp за CDN, прод 2026-10-28)**: полная схема + грабли в `infra/cdn-xhttp.md`. `🇪🇪 1.7x LTE Эстония` = ee. -> CDNvideo -> nginx:443 -> xhttp:9444 (EE-Profile, REALITY-EE на :10443 выключен, multiplier 1.7). `🇩🇪 LTE Германия` = de. -> Yandex CDN -> REALITY self-steal -> nginx:8443 -> xhttp:9444 (Default-Profile, inbound активен только на DE). Ключевая разница extra: DE `uplinkDataPlacement: header` (Яндекс режет тела 413), EE `body` (CDNvideo пропускает).
- Юзер PATCH: `{"id":<int>,"username":"...",...}` (uuid в теле не работает). Кириллицу/emoji в JSON гнать только base64-файлом на сервер (`/tmp/payload-*.json` + `curl -d @file`), через ssh-строку ломается в `?`.
