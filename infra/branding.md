# Брендинг minishop под Proliv Network

Как переодеть завендоренный minishop (`shop/`, upstream `3252a8/remnawave-minishop`)
в Proliv Network **без правок исходников** — через штатные механизмы:
файлы в `/app/data` (docker volume `remnawave-minishop-shop-data`),
DB-оверрайды настроек и админку Web App.

Готовые файлы для локального стенда лежат в `infra/seed/` (см. `infra/seed/README.md`).

## Слои конфигурации (приоритет)

1. **DB-оверрайды** (`app_setting_overrides`, `locale_overrides`) — правятся из
   админки, применяются на лету или после рестарта backend.
2. **Файлы в `/app/data`** — `tariffs.json`, `locales-overrides.json`,
   `legal/*.md`, `webapp-logo/uploads/*`. Для `locales-overrides.json` файл —
   source of truth, БД — только fallback (`backend/bot/services/locale_override_service.py`).
3. **`.env`** — дефолты; то, что есть в манифесте админки, переопределяется из БД.
4. **BotFather** — аватар, описания, список команд, menu button Mini App
   (вне репозитория, чек-лист ниже).

Локальная админка: `http://localhost:8086` (frontend), backend `http://localhost:8085`.
Вход — через webapp-сессию, роль owner/admin в БД (`backend/bot/app/web/admin_api_impl/auth.py`).

---

## 1. Тексты бота

**База:** `shop/locales/ru.json`, `shop/locales/en.json` — НЕ трогаем (vendored).

**Штатный оверрайд (3 способа, один источник):**

| Способ | Где |
|--------|-----|
| Файл | `data/locales-overrides.json` внутри volume (пример — `shop/data/locales-overrides.example.json`) |
| Админка | Web App → Админка → **Система → Переводы** |
| API | `GET/PATCH /api/admin/translations` |

Формат: `{ "ru": { "key": "текст" }, "en": { "key": "text" } }`. Значение —
плоский текст (в `locale_overrides.value` хранится без JSON-кавычек).

**Ключи для Proliv** (плейсхолдеры `{user_name}` и пр. — сохранять!):

| Ключ | Базовое значение (ru) | Предлагаемое Proliv |
|------|----------------------|---------------------|
| `welcome` | `Добро пожаловать, {user_name}!` | `Добро пожаловать в Proliv Network, {user_name}!` |
| `main_menu_greeting` | `Привет, {user_name}! 👋\nПерейдите в "Личный кабинет", ...` | аналог с упоминанием Proliv |
| `menu_personal_account_button` | `🔑 Личный кабинет` | можно оставить; этот же текст используется для TG menu button при регистрации домена (`backend/bot/main_bot.py:178-188`) |
| `menu_support_button` | `💬 Связаться в telegram` | `💬 Поддержка Proliv` |
| `bot_command_start_description` | `Главное меню` | `Proliv Network - главное меню` (или env/override `START_COMMAND_DESCRIPTION`) |
| `bot_command_tg_description` | `Интерфейс бота` | при желании `Proliv` |
| `menu_info_button`, `menu_referral_inline`, `menu_apply_promo_button` и пр. | любые | любые подписи кнопок меняются так же |
| `referral_friend_message*` | шаблоны реф-приглашения | брендировать текстом Proliv |

Потребители: `welcome` — `backend/bot/handlers/user/start_flow.py`,
`main_menu_greeting` — `backend/bot/handlers/user/start_menus.py:79`,
описания команд — `backend/bot/services/telegram_bot_commands.py` (синк при
старте и после смены настроек).

**Название сервиса / ссылки / прочее — runtime-настройки** (админка
**Система → Настройки**, `PATCH /api/admin/settings`, DB `app_setting_overrides`,
значения JSON-encoded):

| Ключ | Назначение | Proliv |
|------|-----------|--------|
| `WEBAPP_TITLE` | заголовок `<title>`, og-теги, `{brand}` в email-футерах | `Proliv Network` |
| `START_COMMAND_DESCRIPTION` | описание `/start` в меню команд | `Proliv Network - главное меню` |
| `SUPPORT_LINK` | куда ведёт кнопка поддержки | `https://t.me/<support>` (подставить реальный) |
| `PRIVACY_POLICY_URL` | ссылка на политику ПД | лучше managed-документ (см. ниже) |
| `USER_AGREEMENT_URL` | ссылка на оферту | лучше managed-документ |
| `DEFAULT_LANGUAGE` | язык по умолчанию | `ru` |
| `TRIAL_ENABLED` | кнопка триала | `false` — по SPEC триал только через промокод/рефералку (`referral_welcome_bonus_tariff` + `REFERRAL_WELCOME_BONUS_DAYS` в тарифном каталоге) |
| `MY_DEVICES_SECTION_ENABLED` | раздел «Мои устройства» | `true` |
| `SERVER_STATUS_ENABLED` | страница статуса серверов | `false`, пока статус-страницы нет |
| `MENU_BUTTONS_JSON` | кастомные кнопки меню (внешние/TG/WebApp/page, локализованные подписи, эмодзи, видимость) — схема `backend/config/menu_buttons.py` | например кнопка «Сайт» на `https://proliv-network.xyz` |
| `TELEGRAM_MENU_APPEARANCE_JSON` | порядок/вид кнопок TG-меню | по вкусу |
| `TELEGRAM_CUSTOM_EMOJI_LIBRARY_JSON` | кастомные TG-эмодзи (id — десятичные строки) — `backend/config/telegram_menu.py` | если есть premium-эмодзи |

**Юрдокументы** (оферта/ПД) — managed-документы, правятся в админке
(раздел документов, API `GET/PUT /api/admin/documents`) или файлами
`data/legal/policy.md`, `data/legal/terms.md`. Резолвер
`backend/bot/services/legal_document_links.py` смотрит сначала в managed-доки,
потом в локальные страницы `/legal/*`, потом в `*_URL` из настроек. Свободные
markdown-страницы — `data/pages/*.md` (`/api/admin/information-pages`).

---

## 2. Webapp-ассеты (лого, фавикон, тема)

Править `shop/frontend/public/` НЕ нужно — всё через админку:

- **Админка → Внешний вид**: загрузка лого, фавикона, выбор темы
  (`ascii/dark/light/windows95` + кастомные), акцентный цвет, шрифт, масштаб лого.
- API: `POST /api/admin/appearance/logo`, `POST /api/admin/appearance/favicon`,
  `GET/PUT /api/admin/themes`.
- Загруженное лого пишется в `data/webapp-logo/uploads/` и проставляется в
  `WEBAPP_LOGO_URL` (`/webapp-uploaded-logo/<hash>.<ext>`). Внешний HTTPS-URL
  тоже можно — backend проксирует его на `/webapp-logo` и кэширует в
  `data/webapp-logo/` (`backend/bot/app/web/webapp/asset_paths.py`).
- Дефолтный бренд-пак (лого+фавиконы) вшит в образ:
  `backend/bot/app/web/templates/default-brand/` — не трогаем, перекрываем
  загрузкой через админку.
- Акцентный цвет: настройка `WEBAPP_PRIMARY_COLOR`. Фирменный акцент Proliv
  из `landing`/`cabinet` — **`#7dd3fc`** (см. `--accent` в
  `landing/assets/css/main.css:15`, `cabinet/assets/css/main.css:15`).

TG-аватар бота сюда не относится — только BotFather.

---

## 3. Тарифы и цены

**Механизм: JSON-каталог, не таблица в БД.**

- Путь: `TARIFFS_CONFIG_PATH`, дефолт `data/tariffs.json` (= `/app/data/tariffs.json`
  в контейнере). Пример: `shop/data/tariffs.example.json`.
- Админка: **Система → Тарифы** (валидирует и атомарно пишет файл,
  инвалидирует кэши — `backend/bot/app/web/admin_api_impl/tariffs.py`).
- API: `GET/PUT /api/admin/tariffs`.
- Схема: `backend/config/tariffs_config.py` (`schema_version: 2`,
  `period_unit: "day"` — периоды задаются в днях: 30/90/180/365).

**Готовый каталог Proliv:** `infra/seed/tariffs.json`. Один тариф `proliv`:

- `billing_model: "period"`, `monthly_gb: 1024` (= 1 ТиБ «1 ТБ»; конверсия
  `* 1024**3` байт — `tariffs_config.py:713`), `hwid_device_limit: 5`.
- `enabled_periods: [30, 90, 180, 365]` = 1/3/6/12 мес.
- `prices_rub`: `30 → 179`; скидка задаётся просто ценой ниже кратной месячной:
  `90 → 499` (~166 ₽/мес), `180 → 949` (~158 ₽/мес), `365 → 1799` (~150 ₽/мес).
  **Цены финальные (утверждены 2026-10-26).**
- `topup_packages.rub`: докупка трафика (100 GB = 49 ₽ / 500 GB = 149 ₽).
- `hwid_device_packages.rub`: +1 устройство 29 ₽/30 дн (`prices` по периодам).
- `checkout_addons.devices`: докупка устройств на чекауте (лимит/цена правятся).
- `referral_bonus_days_*`: бонусные дни рефералки по периодам; welcome-бонус
  реферала — `referral_welcome_bonus_tariff` + настройка
  `REFERRAL_WELCOME_BONUS_DAYS` (это и есть «триал по рефералке» из SPEC).
- `squad_uuids`: UUID **Internal Squads** нашего Remnawave (UK/EE/DE) —
  плейсхолдеры заменить реальными (см. §4).

Валюта по умолчанию `rub`; `prices_stars` можно оставить 0/не задавать, если
Stars-платежей нет.

---

## 4. Локации

**Как мапятся:** локация = Internal Squad в Remnawave. В тарифе поле
`squad_uuids` (и опционально `premium_squad_uuids` для «премиум»-набора).
Список сквадов из панели подтягивается в редакторе тарифов —
`GET /api/admin/panel/internal-squads`. Легаси-ENV `USER_SQUAD_UUIDS` —
фолбэк/дефолт, в сообщениях об ошибках ещё встречается.

**Выбор локации юзером:** в текущем коде **нет** пользовательского выбора
сервера — ни в боте, ни в витрине webapp. Юзер получает сквады своего тарифа;
внутри сквада ноды/локации раздаёт Remnawave.

- Вариант без кода: один сквад на тариф, куда панель кладёт все три локации
  (UK/EE/DE) — пользователь выбирает точку уже в VPN-клиенте по конфигу
  (Remnawave выдаёт все ноды сквада в подписке). **Рекомендовано.**
- Если нужен явный выбор локации в магазине (разные сквады = разные тарифы
  «Proliv UK»/«Proliv EU») — это либо несколько тарифов с разными
  `squad_uuids` (работает из коробки, но удваивает каталог), либо фича-запрос
  в upstream: селектор сквада на чекауте (`squad_uuids` уже умеет несколько
  значений, но они применяются все сразу — нужен UI выбора и запоминание
  выбранного; предположительный дифф — поле выбора в checkout +
  `user_panel_squad_overrides`, таблица уже есть: `db/models.py:117`).

---

## 5. BotFather — чек-лист (вне репозитория)

Что бот **не** делает сам и надо выставить руками в @BotFather:

- [ ] `/setname` — отображаемое имя: `Proliv Network`
- [ ] `/setdescription` — «что умеет бот» (экран перед /start)
- [ ] `/setabouttext` — короткое about в профиле
- [ ] `/setuserpic` — аватар (лого Proliv, 512×512)
- [ ] `/setcommands` — список команд. Бот при старте сам синкает описания
      `/start` и `/tg` (`START_COMMAND_DESCRIPTION` → `bot_command_*_description`),
      но **сам список команд и локализованные описания — в BotFather**
- [ ] **Menu Button / Domain** — привязать Mini App URL
      (`SUBSCRIPTION_MINI_APP_URL`, напр. `https://app.proliv-network.xyz`). При старте
      backend делает `set_chat_menu_button(MenuButtonWebApp)` и сразу возвращает
      `MenuButtonDefault` — это только регистрация домена у Telegram
      (`backend/bot/main_bot.py:182-188`); постоянную кнопку меню задаёт BotFather.
- [ ] `/setdomain` — если потребуется для Web App домена.
- [ ] `/setinline*` / платежные провайдеры — если будут нужны.

---

## 6. Иконки меню бота (Android/Material, как у Ranteis)

Смайлики в кнопках заменены на кастомные иконки из пака
**Telegram Android Icons** — `https://t.me/addemoji/TgAndroidIcons`
(515 иконок, Material-стиль). Настройки живут в БД
(`app_setting_overrides`), не в `.env`:

- `TELEGRAM_CUSTOM_EMOJI_LIBRARY_JSON` — `{"sets":["TgAndroidIcons"]}`.
- `TELEGRAM_MENU_APPEARANCE_JSON` — на каждую кнопку: `icon_custom_emoji_id`
  (ID иконки из пака), `icon_mode` (`custom`/`none`/`inherit`), `style`
  (`primary` = синяя как «Подключиться» у Ranteis, `success`, `danger`).

Редактировать визуально: `http://127.0.0.1:8086/admin` →
**Telegram menu** (раздел menu_buttons): пикер с превью иконок,
тест-отправка себе в чат. ID всех иконок пака — `infra/TgAndroidIcons.txt`
(дамп `getStickerSet`, формат `custom_emoji_id<TAB>fallback-emoji`).

Регенерация маппинга: `infra/gen_menu_appearance.py` — правим
`APPEARANCE` dict, дальше:

```powershell
type infra\gen_menu_appearance.py | docker exec -i remnawave-minishop-backend python - | Out-File -Encoding ascii infra\menu_appearance.sql
Get-Content infra\menu_appearance.sql | docker exec -i remnawave-minishop-postgres psql -U remnawave_minishop -d remnawave_minishop -v ON_ERROR_STOP=1
docker compose -f shop/docker-compose.yml -f infra/minishop.compose.yml --env-file shop/.env up -d backend bot
```

Ограничение Telegram: `icon_custom_emoji_id` в кнопках и custom-emoji
сущности в текстах работают только если **владелец бота имеет Premium**
(или бот купил доп-юзернеймы на Fragment). Иначе minishop молча фолбэчит
на обычные unicode-эмодзи (`bot/app/factories/telegram_custom_emoji.py`) —
меню не ломается, просто иконки дефолтные.

Смайлики в текстах сообщений — это строки локалей (`locales/ru.json` и т.д.).
Переопределяются в админке → Translations (DB-таблица locale overrides,
`bot/services/locale_override_service.py`); в тексте можно вставлять
кастомные эмодзи тегом `<tg-emoji emoji-id="...">🙂</tg-emoji>`.

## 7. Что остаётся за пользователем

1. Реальные UUID Internal Squads UK/EE/DE из панели → `squad_uuids` в
   `infra/seed/tariffs.json` (или правка в админке: там сквады подгружаются
   из панели списком).
2. Финальные цены 3/6/12 мес и топ-апы (в файле — плейсхолдеры).
3. Лого/фавикон Proliv → загрузить в **Внешний вид** (или дать HTTPS-URL в
   `WEBAPP_LOGO_URL`).
4. Тексты оферты и политики ПД — managed-документы в админке.
5. `SUPPORT_LINK` — реальный TG-канал/бот поддержки.
6. BotFather-чек-лист (§5).
7. Прода: `SUBSCRIPTION_MINI_APP_URL=https://app.proliv-network.xyz` в `shop/.env`
   (env-файлы правит только пользователь — см. AGENTS.md).
8. После сида/правки файлов — рестарт `backend`+`worker`
   (`docker restart remnawave-minishop-backend remnawave-minishop-worker`).

## 8. Ограничения (без правки кода не сделать)

- Выбор локации внутри тарифа на чекауте — нет такого UI (§4).
- Картинка-баннер в приветствии бота — `welcome` текстовый; баннеры есть только
  в рассылках/поддержке.
- Системные коды ошибок/техтексты вне локалей — как у upstream.
