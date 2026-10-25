# TG-бот продаж: выбор форка и подключение к compose

> Дата ресёрча: 2026-10-25. Оригинал `machka-pasla/remnawave-tg-shop` (позже `kavore/remnawave-tg-shop`) архивирован; последняя проверенная им версия панели - Remnawave 2.6.4.

## Выбранный форк

**Jolymmiels/remnawave-telegram-shop** - независимое переписывание на Go (не git-форк, но тот же класс решения и упомянут в README архивного репо через экосистему форков).

- Репо: https://github.com/Jolymmiels/remnawave-telegram-shop
- Документация: https://docs.rwp.rw/ru/
- Образ: `ghcr.io/jolymmiels/remnawave-telegram-shop-bot:5.1.0` (есть теги `latest`, `5`, semver; multi-arch amd64/arm64)
- Лицензия: AGPL-3.0
- Текущая версия: **5.1.0** (релиз 06.09.2026; пин версии вместо `latest` рекомендован)

### Почему именно он

| Критерий | Jolymmiels/remnawave-telegram-shop | VAQYBIN/remnawave-tg-shop | 3252a8/remnawave-minishop |
|---|---|---|---|
| Stars / forks | **359 / 70** | 13 / 5 | основной репо на GitLab, GH-зеркало kinm ~0 |
| Активность | релизы до сен 2026 (5.1.0), живой CI | ~606 коммитов, README свежий | коммиты еженедельно, очень активный |
| Remnawave v3 | **да** - с 5.0.0 (клиент на API v3.4.x) | **да** - только 3.x (3.2.1-3.4.3) | вопрос требует проверки |
| YooKassa | да, на вебхуках (с 4.1.0) | да | да |
| Telegram Stars | да | да | да |
| Прочие платежи | CryptoPay, Tribute, Platega (СБП/карты/крипта) | LavaPay, FreeKassa, CryptoPay, Platega, SeverPay | CryptoPay и др. |
| Docker-образ | `ghcr.io/jolymmiels/remnawave-telegram-shop-bot` | `ghcr.io/vaqybin/remnawave-tg-shop` (+web-api, +web-frontend) | compose-стек из репо |
| Mini App | только ссылка на внешний (`MINI_APP_URL` + `IS_WEB_APP_LINK`) | **встроенный** веб-кабинет + TG Mini App (initData) | **встроенный** webapp |
| Стек/вес | Go + PostgreSQL (2 контейнера) | Python/Aiogram + FastAPI + React + PG + Redis (5 контейнеров) | тяжёлый стек backend+frontend |
| Telegram-режим | **long polling** (домен не нужен) | webhook (нужен публичный домен) | - |

Решение: Jolymmiels - самый поддерживаемый и самый лёгкий вариант, совместимый с нашей панелью `remnawave/backend:3` (матрица: бот 5.0.x-5.1.x = панель 3.4.x). Свой Mini App мы всё равно планируем кастомный под бренд (SPEC раздел 8), встроенный кабинет VAQYBIN дублирует эту работу и тянет 5 контейнеров + обязательный публичный webhook-домен. Если захотим готовый кабинет без своей разработки - VAQYBIN остаётся запасным вариантом (его prod-compose тоже рассчитан на external-сеть `remnawave-network`).

## Как это работает

- Два сервиса: `tg-shop` (бот) + `tg-shop-db` (PostgreSQL 17, отдельный от `remnawave-db` - у бота свои таблицы покупателей/покупок/рефералов).
- Миграции БД применяются самим ботом при старте (`db/migrations` внутри образа).
- Бот ходит в API панели по внутреннему адресу `http://remnawave:3000` в сети `remnawave-network`. Заголовки `x-forwarded-for: 127.0.0.1` / `x-forwarded-proto: https` клиент бота подставляет автоматически для хостов `remnawave*` (даже при `REMNAWAVE_MODE=remote`).
- Авторизация в панели: `Authorization: Bearer <REMNAWAVE_TOKEN>` - API-токен создаётся в панели (Settings -> API Tokens).
- Образ `FROM scratch`, юзер UID 1000, `DISABLE_ENV_FILE=true` уже выставлен - конфиг только через env контейнера (наш `env_file`).
- Переводы и миграции запечены в образ (`/translations`, `/db`); маунт `./translations` нужен только для кастомизации текстов.

## Тарифы и ограничения модели

- В боте жёстко 4 тарифных слота: `PRICE_1/3/6/12` (RUB) и `STARS_PRICE_1/3/6/12` (Stars). Все четыре `PRICE_*` обязательны. Наш тариф 179 руб/мес = `PRICE_1`; остальные слоты заполняем своими ценами или ставим заведомо "невыгодные" значения до решения по скидкам (открытый вопрос SPEC).
- `TRAFFIC_LIMIT`/`TRIAL_TRAFFIC_LIMIT` - в ГБ (умножаются на 2^30 внутри). Наш 1 ТБ = `1024`.
- `TRAFFIC_LIMIT_RESET_STRATEGY=MONTH` - ежемесячный сброс лимита (DAY/WEEK/MONTH/NO_RESET).
- Пробный период: `TRIAL_DAYS` + `TRIAL_TRAFFIC_LIMIT` обязательны (SPEC открытый вопрос 7 - по умолчанию 3 дня / 10 ГБ).
- `SQUAD_UUIDS` пустой = бот назначает юзеру все internal-сквады панели. Когда появится отдельный сквад для клиентов - перечислить UUID через запятую. `EXTERNAL_SQUAD_UUID` - опционально.
- `ADMIN_TELEGRAM_ID` - **один** числовой TG ID (в коде `strconv.ParseInt`, список не поддерживается).

## Что требует публичного домена, а что нет

- **Telegram Bot API - long polling.** Бот сам опрашивает api.telegram.org, входящих соединений нет. Локальная разработка работает без домена и без туннелей. Один токен = один polling-инстанс (не поднимать два контейнера с одним токеном).
- **HTTP-сервер бота** слушает `HEALTH_CHECK_PORT` (дефолт 8080) и отдаёт:
  - `GET /healthcheck` - JSON-статус бота + пинг БД и панели (смотреть с хоста: `http://127.0.0.1:8090/healthcheck`);
  - `YOOKASA_WEBHOOK_URL` - путь вида `/webhook/yookassa/<случайный-секрет>`;
  - `PLATEGA_WEBHOOK_URL`, `TRIBUTE_WEBHOOK_URL` - аналогично.
- **YooKassa** подтверждает оплату только вебхуком (polling убрали в 4.1.0): нужен публичный HTTPS-адрес, напр. `https://bot.proliv.net/webhook/yookassa/<secret>` -> реверс-прокси на `127.0.0.1:8090`. URL регистрируется в кабинете YooKassa ("Интеграция" -> "HTTP-уведомления", события `payment.succeeded`, `payment.canceled`). Секрет в пути генерить `openssl rand -hex 32`.
- **Telegram Stars** не требует домена (оплата внутри Telegram) - единственный способ оплаты, работающий на локалке end-to-end.
- **CryptoPay** - confirm идёт polling-джобой внутри бота, вебхук не нужен.
- Итог по доменам: для dev достаточно Stars/CryptoPay. Для прод-эквайринга картами нужен `bot.<domain>` (или путь на существующем домене) с HTTPS до порта 8090.

## Шаги подключения к нашему compose

1. `cp infra/tg-shop.env.example infra/tg-shop.env`, заполнить (минимум: `TELEGRAM_TOKEN`, `ADMIN_TELEGRAM_ID`, `POSTGRES_PASSWORD` + `DATABASE_URL`, `REMNAWAVE_TOKEN`).
2. В панели Remnawave: Settings -> API Tokens -> создать токен (проще всего с полными правами; иначе нужны scopes на users read/write, internal-squads read, system) -> в `REMNAWAVE_TOKEN`.
3. В `docker-compose.yml` вставить сервисы из `infra/tg-shop.compose.yml` (там закомментировано что переносить: `services`, и добавить `tg-shop-db-data` в `volumes`). Либо без правки основного файла: `docker compose -f docker-compose.yml -f infra/tg-shop.compose.yml up -d` (файл самодостаточен, сеть объявлена external).
4. `docker compose up -d` -> логи `docker logs tg-shop`, дождаться `Bot is starting` / проверить `curl http://127.0.0.1:8090/healthcheck` (`status: ok`, `db: ok`, `rw: ok`).
5. В TG: `/start` боту -> проверка триала/покупки Stars.
6. YooKassa для прода: завести магазин на самозанятого, заполнить `YOOKASA_*`, прокинуть `bot.<domain>` -> `127.0.0.1:8090`, зарегистрировать вебхук в кабинете ЮKassa.
7. Чеки самозанятого (54-ФЗ) без кассы ЮKassa: блок `MOYNALOG_*` (lknpd.nalog.ru API) - релевантно нам, самозанятость есть (SPEC раздел 2).

## Матрица совместимости (из docs.rwp.rw)

| Панель Remnawave | Версия бота |
|---|---|
| 2.8.* | 4.1.* |
| **3.4.x** | **5.0.x - 5.1.x** |

Наш `remnawave/backend:3` -> бот **5.1.0**. Перед обновлением панели сверяться с матрицей: мажорная версия панели и мажор бота идут в связке.

## Ссылки

- Бот: https://github.com/Jolymmiels/remnawave-telegram-shop
- Доки и справочник env: https://docs.rwp.rw/ru/
- Пакеты/теги образа: https://github.com/Jolymmiels/remnawave-telegram-shop/pkgs/container/remnawave-telegram-shop-bot
- SDK панели (совместимость API): https://github.com/Jolymmiles/remnawave-api-go
- Запасные форки: https://github.com/VAQYBIN/remnawave-tg-shop (встроенный Mini App + веб-админка, webhook-only, 5 контейнеров), https://gitlab.com/3252a8/remnawave-minishop (webapp+bot, активная разработка на GitLab)
