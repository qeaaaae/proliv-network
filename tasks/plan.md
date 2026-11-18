# План: корпоративный тариф (corp)

> Спека: `SPEC-corporate.md`. Реализация внутри `shop/` (vendored fork - держать весь новый код в отдельных corp-файлах, точки входа в upstream-файлы минимальны) и `cabinet/`.

## Подход

Корп-доступ - это не новый вид подписки в тарифном каталоге, а отдельный домен: группа владеет слотами, участники получают штатную подписку+panel-юзера, управляемую корп-сервисом (expire = period_end группы, DAY-стратегия, квота). Все механики ложатся на существующие стыки minishop; новый код изолируем в `corp_*` модули.

## Стыки с существующим кодом

| Задача | Куда цепляемся |
|---|---|
| Таблицы | `db/corp_models.py` + `db/dal/corp_dal.py` + `chain_0114_corp_groups.py` (след. номер 0114, append-only), re-export в `db/models.py` - паттерн `giveaway_models.py`/`admin_purchase_models.py` |
| Диплинк-инвайт | `start_flow.py`: добавить regexp `^corp_([A-Za-z0-9_-]+)$` + вызов `join_corp_from_start` - паттерн `giveaway_match`/`join_giveaway_from_start` |
| Провижининг участника | SubscriptionService: подписка (expire=group.period_end) + panel user (squad корп-тарифа, `traffic_limit_strategy=DAY`, `trafficLimitBytes=квота`). Переиспользовать `lifecycle_activation`/`panel_api_users` обвязки |
| Вкл/выкл доступа | `panel_api_users` `/users/{uuid}/actions/{enable,disable}` - готово |
| Квота | update panel user `trafficLimitBytes` (обвязка есть в `panel_api_users` ~730) |
| Создание платежа | `billing_payments.py` пайплайн: sale_mode `corp@<group_id>` + snapshot `{kind: base|renew|seat}`; провайдер-агностичный create |
| Фулфилмент | `payment_providers/shared/independent_success.py` -> `resolve_corp_payment(req)` рядом с `resolve_gift_payment`; `is_corp_sale()` по `sale_mode` (как `is_gift_sale` - теги после `|`) |
| Webapp API | `webapp/routes.py` + модуль `webapp/corp.py` (+`corp_contracts.py`); auth: `_require_user_id` + проверка "юзер - админ группы" в corp-сервисе |
| Кабинет BFF | `cabinet/server/api/corp/[...].ts` - копия `admin/[...].ts`, прокси на `/api/corp/*` |
| Кабинет UI | `cabinet/pages/corp.vue` (раздел виден только group-admin), компоненты `cabinet/components/corp/*`; карточка участника в overview |
| Уведомления | DM через `send_success_message_to_user`-подобные хелперы/queue_manager; дедуп по `subscription_notifications`-ключам или `message_logs` |
| Цены | `tariffs.json` корп-запись `corp` с кастом-полями (base_price 2300, extra_seat_price 200, base_slots 10) - читает corp-сервис, чтобы цены правились через админку без релиза |

## Порядок и зависимости

1. **corp-core**: модели+миграция+DAL+`corp_group_service` (группы, слоты, инварианты). Ни от чего не зависит.
2. **corp-quota/provisioning**: выдача entitlement участнику + квота + enable/disable. Зависит от core. Самый рискованный стык (см. риски) - делать сразу после core.
3. **corp-billing**: checkout-роут -> Payment(sale_mode corp) -> fulfillment -> создание группы/продление/докупка слота. Зависит от core+quota.
4. **corp-invites**: диплинк + username-инвайты + занятие слота. Зависит от provisioning.
5. **corp-admin-api**: `/api/corp/*` роуты. Зависит от всего выше.
6. **corp-cabinet-ui**: BFF-прокси + страница админа группы + карточка участника + заглушка покупок. Зависит от API.
7. **corp-bot**: DM-уведомления. Можно параллельно с 5-6.

Verification checkpoints: после 1-2 - pytest DAL/сервиса; после 3 - юнит-тесты биллинга (прорация, renewal-сумма) + локальный E2E оплаты; после 4 - E2E инвайта двумя тест-юзерами; после 6 - ручной прогон кабинета; финал - `pytest`, `ruff check backend`, `mypy backend`, `cd cabinet && npx nuxi typecheck`.

## Риски

- **Провижининг без платежа**: участник получает подписку не через payment-activation. Нужен corp-путь создания Subscription row + panel user. Перед кодом - прочитать `lifecycle_activation.py` и выбрать: тонкий corp-provisioning через subscription_service или прямое создание + `sync_main_traffic_limit_to_panel`. Митигейшн: E2E-тест "инвайт -> юзер в панели с DAY-квотой".
- **Гонка за последний слот**: принятие инвайта - под `SELECT ... FOR UPDATE` группы/счётчика слотов или unique-partial-index на занятые слоты.
- **Продление = массовый panel sync**: на N участников N update-вызовов expire. Делать транзакцией БД + последовательный panel sync; при падении - повторяемый worker/retry (как tariff sync). Лимит группы в v1 - десятки участников, ок.
- **DAY-стратегия панели**: момент сброса не задокументирован у нас - проверить фактом на тест-юзере, текст в кабинете подстроить (открытый вопрос #2 спеки).
- **Vendored fork**: upstream-файлы трогаем только в точках регистрации (routes.py, independent_success.py, start_flow regexps, models re-export, openapi regen). Все corp-файлы - отдельные, префикс `corp_`.
- **Локали**: каждый user-facing ключ -> ru.json+en.json (правило shop), + `corp_`-префикс в locale_override_service если нужен оверрайд через админку.
- **Кабинет**: новые user-facing роуты попадают под rate-limit/CSRF-правила webapp - проверить `csrf_origin.py`/`resource_middleware.py` не нужно ли расширение whitelist.

## Объём (грубо)

- Backend: ~8 новых файлов (models, dal, 2-3 сервиса, webapp-роуты+контракты, bot-хендлер) + ~6 точечных правок upstream + миграция.
- Cabinet: 1 BFF-прокси + 1-2 страницы + ~4 компонента + правки overview/purchases.
- Тесты: DAL, сервисные инварианты, биллинг-математика, инвайт-флоу.
