# YooKassa в minishop - e2e инструкция

Как поднять приём платежей через ЮKassa в нашем стеке (vendored
`shop/` = форк 3252a8/remnawave-minishop). Цель: остаётся вставить ключи.

Код провайдера: `shop/backend/bot/payment_providers/yookassa/`.
Метод-id платежа: **`yookassa`** (в `POST /api/payments` поле `method`).
Цены: рубли, десятично (`"179.00"` в API ЮKassa). Валюта: только **RUB**
(hardcode в `SPEC.supported_currencies`; не-RUB платёж отклоняется с
`unsupported_currency` до вызова API).

---

## 1. Что регистрируем в ЮKassa

1. `yookassa.ru` -> регистрация магазина. Для самозанятого (НПД) ЮKassa
   умеет работать напрямую - при подключении выбирается статус
   самозанятого, договор онлайн.
2. После регистрации в кабинете доступен **тестовый магазин** - у него
   свой shopId и секрет `test_...`. Сначала гоняем его, потом боевой
   (`live_...`). Отдельного флага "test mode" в коде нет - режим
   определяется парой ключей. В тестовом магазине деньги не списываются,
   доступны только банковские карты и ЮMoney (СБП не тестируется).
3. Ключи: **ЛК ЮKassa -> магазин -> Интеграция -> API-ключи**
   (`shopId` + секретный ключ).

## 2. Переменные окружения (shop/.env или админка)

Минимум для включения (все ключи уже задекларированы в
`infra/minishop.env.example`):

| Переменная | Значение |
|---|---|
| `YOOKASSA_ENABLED` | `True` (дефолт True - ключи вставил = провайдер включился) |
| `YOOKASSA_SHOP_ID` | shopId из ЛК ЮKassa |
| `YOOKASSA_SECRET_KEY` | `test_...` / `live_...` |
| `YOOKASSA_RETURN_URL` | куда вернуть плательщика; дефолт `https://t.me/<bot_username>`, без бота задай `PUBLIC_APP_URL` |
| `YOOKASSA_DEFAULT_RECEIPT_EMAIL` | **обязательно**: без контакта чека создание платежа падает `receipt_contact_missing` |
| `YOOKASSA_VAT_CODE` | `6` = без НДС (самозанятый/УСН без НДС) |

Опциональные:

- `YOOKASSA_PAYMENT_MODE`, `YOOKASSA_PAYMENT_SUBJECT` - переопределение
  полей чека (дефолты: `full_prepayment`/`payment`, с автоплатежами
  `full_payment`/`service`). Только через env - в админке их нет.
- `YOOKASSA_AUTOPAYMENTS_ENABLED=True` + `YOOKASSA_AUTOPAYMENTS_REQUIRE_CARD_BINDING`
  - автопродление по сохранённой карте. Требует включённых рекуррентов в
  договоре ЮKassa.
- `YOOKASSA_ADMIN_ONLY_ENABLED=True` - способ виден только `ADMIN_IDS`
  (удобно для боевого теста до публичного запуска).
- `PAYMENT_YOOKASSA_WEBAPP_LABEL_RU` / `..._EN`, `PAYMENT_YOOKASSA_WEBAPP_ICON`,
  `PAYMENT_YOOKASSA_TELEGRAM_LABEL_*`, `PAYMENT_YOOKASSA_TELEGRAM_EMOJI` -
  подпись/иконка кнопки оплаты.
- `PAYMENT_METHODS_ORDER` - порядок в списке способов (слаг `yookassa`).

Все ключи секции YooKassa кроме `PAYMENT_MODE`/`PAYMENT_SUBJECT` есть в
манифесте настроек и правятся без рестарта:
**Админка -> Система -> Настройки -> Платежи -> YooKassa** (значения
персистятся в БД поверх env). Там же вверху раздела показывается готовый
webhook URL.

## 3. Webhook

- Путь: **`POST /webhook/yookassa`** на webhook-порту backend
  (внутри контейнера `:8080`; на хосте - `$WEB_SERVER_PORT`, сейчас 8087).
- Роут регистрируется **только если задан `WEBHOOK_BASE_URL`**
  (`webhook_requires_base_url=True` в SPEC; проверено в логах:
  `YooKassa webhook route configured at: [POST] /webhook/yookassa`).
- В кабинете ЮKassa: **Интеграция -> HTTP-уведомления** ->
  `https://<публичный-домен>/webhook/yookassa`. Нужен публичный HTTPS -
  localhost ЮKassa не достучится. События для подписки:
  `payment.succeeded`, `payment.canceled`, `payment.waiting_for_capture`
  (последнее нужно только при автоплатежах/привязке карт).
- `WEBHOOK_BASE_URL` в ЮKassa никуда не отправляется - URL вбивается
  руками в кабинете; переменная лишь включает роут и показывается в
  админке как подсказка.
- **Проверки входящего вебхука**: подписи у ЮKassa нет - фильтрация по
  IP-allowlist, зашитому в код
  (`185.71.76.0/27`, `185.71.77.0/27`, `77.75.153.0/25`, `77.75.156.11`,
  `77.75.156.35`, `77.75.154.128/25`, `2a02:5180::/32`) + сверка
  `metadata.payment_db_id`, суммы и валюты с локальным заказом. Чужой
  IP -> `403` до парсинга.
- За реверс-прокси/туннелем: прокси должен прокидывать `X-Forwarded-For`,
  а его адрес/имя - входить в `TRUSTED_PROXIES` (дефолт: `127.0.0.1`,
  `::1`, `host:frontend`, `host:caddy`, `host:nginx`, `host:angie`,
  `host:newt`, `host:newt-2`). Туннель до 127.0.0.1 уже покрыт.
- **Fallback**: если webhook не пришёл/упал, `YooKassaReconciliationWorker`
  в контейнере `worker` сам опрашивает API каждые ~60с (grace 30с) и
  доводит платёж. Тюнинг: `YOOKASSA_RECONCILIATION_TICK_SECONDS`,
  `..._GRACE_SECONDS`, `..._BATCH_SIZE`.

### Стенд без Telegram (TELEGRAM_ENABLED=False)

В апстриме хендлер `/webhook/yookassa` падал 500 на `KeyError: 'bot'` -
роут требовал `bot` из app context, а тот ставится только при поднятом
TG-боте. В нашем форке это исправлено минимальным патчем:
`app_required` -> `app_optional` для `bot` в
`shop/backend/bot/payment_providers/yookassa/webhook.py` (downstream
`process_successful_payment`/`process_cancelled_payment` принимают
`bot: Bot | None`). Если форк когда-нибудь подтянут из апстрима без этого
патча - симптом вернётся; платёж всё равно доведёт
reconciliation-worker за ~1-2 минуты, но webhook будет 500-кать и ЮKassa
будет слать ретраи.

## 4. Фискализация (самозанятый)

Два независимых слоя:

1. **Receipt внутри платежа ЮKassa** - backend всегда шлёт объект
   `receipt` при создании платежа (`service.py`, `builder.set_receipt`).
   Контакт берётся из `payer_email`/`payer_phone` чекаута либо из
   `YOOKASSA_DEFAULT_RECEIPT_EMAIL`. Поля чека: `VAT_CODE`,
   `PAYMENT_MODE`, `PAYMENT_SUBJECT`. Это данные 54-ФЗ для кассы ЮKassa -
   актуально, если в договоре подключена онлайн-касса/"чеки для
   самозанятых". Само по себе наличие блока receipt в запросе ошибкой не
   является - но без контакта платёж не создаётся вовсе.
2. **LKNPD ("Мой налог")** - отдельная регистрация дохода после
   успешной оплаты: backend ходит в `lknpd.nalog.ru` и создаёт чек НПД
   (`lknpd_service` -> `LknpdClient`, auth по ИНН+пароль). Включается:
   - `NALOGO_INN` - ИНН самозанятого
   - `NALOGO_PASSWORD` - пароль от lknpd.nalog.ru
   - `NALOGO_API_URL` - дефолт `https://lknpd.nalog.ru/api`
   - `NALOGO_RECEIPT_NAME_SUBSCRIPTION` / `NALOGO_RECEIPT_NAME_TRAFFIC` -
     шаблоны названия товара (`{months}` / `{gb}`).
   (Alias'ы `LKNPD_INN`/`LKNPD_PASSWORD` тоже читаются, но документируем
   каноничные `NALOGO_*`.)

Для самозанятого правильный путь - (2). Чек НПД создаётся в "Мой налог"
независимо от того, что ЮKassa делает со своим receipt.

## 5. Тариф Proliv Network (179 руб/мес, 3 устройства, 300 ГБ)

Цены живут НЕ в env: каталог тарифов - JSON `/app/data/tariffs.json`
(volume `shop-data`), путь из `TARIFFS_CONFIG_PATH` (дефолт
`data/tariffs.json`). Редактор - **Админка -> Тарифы**
(`PUT /api/admin/tariffs` пишет файл и гоняет реконсиляцию подписок).

Минимальный каталог под спеку (period-тариф, месячный ресет трафика):

```json
{
  "schema_version": 2,
  "period_unit": "month",
  "default_tariff": "proliv_network",
  "default_currency": "rub",
  "tariffs": [
    {
      "key": "proliv_network",
      "names": { "ru": "Proliv Network", "en": "Proliv Network" },
      "descriptions": {
        "ru": "Универсальный Network: 3 устройства, 300 ГБ/мес с переносом остатка",
        "en": "Universal Network: 3 devices, 300 GB/mo with rollover"
      },
      "billing_model": "period",
      "enabled": true,
      "monthly_gb": 300,
      "traffic_limit_strategy": "MONTH_ROLLING",
      "traffic_rollover": true,
      "hwid_device_limit": 3,
      "enabled_periods": [1, 3, 6, 12],
      "prices_rub": { "1": 179, "3": 499, "6": 949, "12": 1799 },
      "topup_packages": {
        "rub": [
          { "gb": 100, "price": 49 },
          { "gb": 500, "price": 149 }
        ]
      },
      "hwid_device_packages": {
        "rub": [
          {
            "count": 1,
            "price": 29,
            "prices": { "1": 29, "3": 87, "6": 174, "12": 348 }
          }
        ]
      }
    }
  ]
}
```

Примечания:

- `period_unit: "month"` -> ключи цен и `enabled_periods` в месяцах.
  Можно `"day"` с ключами `30/90/180/365` - эквивалентно.
- `squad_uuids` тарифа заполнить UUID внутренних сквадов панели
  (UK/EE/DE), иначе юзер не попадёт в нужные сквады; premium-поля не
  нужны - в спеке один тариф без premium-слоёв.
- Докупка трафика (`topup_packages`) и устройств (`hwid_device_packages`)
  работает только через каталог тарифов. **Не задавать `TRAFFIC_PACKAGES`
  в env** - в legacy-режиме (без tariffs.json) эта переменная переключает
  весь магазин в "продажу гигабайт" вместо подписок
  (`traffic_sale_mode`).
- Legacy-фолбэк без каталога (не нужен нам): `RUB_PRICE_1_MONTH`,
  `RUB_PRICE_3_MONTHS`, `RUB_PRICE_6_MONTHS`, `RUB_PRICE_12_MONTHS`,
  `USER_HWID_DEVICE_LIMIT`, `USER_TRAFFIC_LIMIT_GB`,
  `USER_TRAFFIC_STRATEGY`.

## 6. Проверка на локальном стенде

```powershell
# 1. Токен (email-логин dev-стенда)
$resp = curl.exe -s -X POST "http://127.0.0.1:8086/api/auth/email/password" `
  -H "Content-Type: application/json" `
  --data-binary '{"email":"dev@proliv.dev","password":"admin12345"}' | ConvertFrom-Json
$token = $resp.token

# 2. После вставки ключей и пересоздания backend в /api/me должен
#    появиться метод yookassa (сейчас там только stars)
curl.exe -s "http://127.0.0.1:8086/api/me" -H "Authorization: Bearer $token" `
  -H "Accept: application/json" -H "Accept-Encoding: identity"

# 3. Создать платёж -> вернёт payment_url (редирект-форма ЮKassa)
curl.exe -s -X POST "http://127.0.0.1:8086/api/payments" `
  -H "Authorization: Bearer $token" -H "Content-Type: application/json" `
  -H "X-CSRF-Token: $($resp.csrf_token)" `
  --data-binary '{"method":"yookassa","months":1,"sale_mode":"subscription"}'

# 4. Статус платежа
curl.exe -s "http://127.0.0.1:8086/api/payments/<payment_id>" -H "Authorization: Bearer $token"
```

Оплата на тестовой форме ЮKassa: карта `5555 5555 5555 4477`
(Mastercard+3DS) или `4111 1111 1111 1111` (Visa без 3DS), срок - любая
будущая дата, CVC и 3DS-код - любые цифры. Карты для отказов (3d_secure_failed,
card_expired, insufficient_funds и т.д.) - таблица в
[yookassa.ru/developers/.../testing](https://yookassa.ru/developers/payment-acceptance/testing-and-going-live/testing).

После оплаты: webhook `POST /webhook/yookassa` (в логах backend виден
входящий POST) либо догонит worker-сверка ~60с. Проверка статуса:
`GET /api/payments/<id>` -> `succeeded`, подписка активна в `/api/me`.

## 7. Чек-лист ввода в прод

- [ ] `YOOKASSA_SHOP_ID` + `YOOKASSA_SECRET_KEY` (live) в shop/.env или
      админке; `YOOKASSA_ENABLED=True`
- [ ] `YOOKASSA_DEFAULT_RECEIPT_EMAIL` задан
- [ ] `YOOKASSA_VAT_CODE=6` (самозанятый, без НДС)
- [ ] `YOOKASSA_RETURN_URL` = публичный URL мини-аппа (или бот по
      дефолту при включённом Telegram)
- [ ] `WEBHOOK_BASE_URL` = `https://<webhook-домен>`; в кабинете ЮKassa
      указан `<WEBHOOK_BASE_URL>/webhook/yookassa`; прокси в
      `TRUSTED_PROXIES` и прокидывает `X-Forwarded-For`
- [ ] `NALOGO_INN`/`NALOGO_PASSWORD` - если чеки НПД через "Мой налог"
- [ ] Тарифный каталог создан (Админка -> Тарифы), сквады прописаны
- [ ] Тестовый платёж в тестовом магазине -> `succeeded`, чек НПД создан,
      подписка выдана; затем то же на live-ключах с реальной картой
      (при желании сначала `YOOKASSA_ADMIN_ONLY_ENABLED=True`)

## 8. Типичные ошибки

| Симптом | Причина |
|---|---|
| Платёж не создаётся, лог `receipt_contact_missing` | Нет `YOOKASSA_DEFAULT_RECEIPT_EMAIL` и юзер не дал email/телефон |
| Webhook `403` | IP ЮKassa не прошёл allowlist - чаще всего прокси не в `TRUSTED_PROXIES` и backend видит IP прокси |
| Webhook `500 KeyError: 'bot'` | Апстримный баг при `TELEGRAM_ENABLED=False`; в нашем форке исправлен (см. §3). Если вернулся после pull из апстрима - платёж всё равно доведёт worker (~60-90с) |
| Webhook `404`/роута нет | `WEBHOOK_BASE_URL` пуст - роут не регистрируется |
| Способа нет в `/api/me` | Не заданы SHOP_ID/SECRET_KEY (`service.configured=False`) или `YOOKASSA_ENABLED=False` |
| `unsupported_currency` при создании | Попытка продать не в RUB - у провайдера только RUB |
| Автопродление не списывает | Нужны `YOOKASSA_AUTOPAYMENTS_ENABLED` + разрешение рекуррентов в договоре ЮKassa |
| `YooKassa SDK call timed out` | API ЮKassa тормозит; таймаут - `PAYMENT_REQUEST_TIMEOUT_SECONDS` (20с) |

Ссылки: upstream-документация `shop/docs/features/payments.md`,
`shop/docs/configuration/env-vars.md` (раздел YooKassa).
