# Tasks: корпоративный тариф (corp)

План: `tasks/plan.md`. Спека: `SPEC-corporate.md`. Порядок = зависимости.

## Блок A - corp-core

- [ ] Task: Миграция + модели + DAL (`corp_groups`, `corp_seats`, `corp_invites`)
  - Acceptance: таблицы создаются chain-миграцией 0114, модели типизированы, DAL-CRUD покрыт базово
  - Verify: `pytest tests/ -k corp` (новые тесты DAL), `mypy backend`
  - Files: `shop/backend/db/corp_models.py`, `shop/backend/db/dal/corp_dal.py`, `shop/backend/db/migrator/chain_0114_corp_groups.py`, re-export в `shop/backend/db/models.py`, тест

- [ ] Task: `corp_group_service` - жизненный цикл группы и слотов
  - Acceptance: create_group(admin) -> 1 admin-seat + 10 free base; occupy/free seat с инвариантами; extra-seat add/remove (pending_removal до period_end); расчёт цены продления `2300+200*extra`
  - Verify: юнит-тесты сервиса (инварианты, гонка за слот под FOR UPDATE), mypy
  - Files: `shop/backend/bot/services/corp_group_service.py`, тест

## Блок B - provisioning и квота

- [ ] Task: Corp-provisioning участника (подписка + panel user)
  - Acceptance: по занятию слота у юзера появляется Subscription (expire=group.period_end, tariff=corp) и panel user в squad корп-тарифа с `traffic_limit_strategy=DAY`, `trafficLimitBytes=quota`; повторный вызов идемпотентен
  - Verify: тест provisioning + ручная проверка юзера в панели локально
  - Files: `shop/backend/bot/services/corp_provisioning.py`, точечные правки `subscription_service_impl/*` при необходимости, тест

- [ ] Task: Квота и доступ участника
  - Acceptance: `set_member_quota` -> panel `trafficLimitBytes`; `set_member_access` -> enable/disable + `access_disabled` флаг на слоте; ошибки панели -> понятная ошибка, состояние не расходится (read-back как в enable/disable)
  - Verify: юнит-тесты + ручной тогл на панели
  - Files: `shop/backend/bot/services/corp_access.py`, тест

## Блок C - billing

- [ ] Task: Corp-чекаут: `POST /api/corp/checkout` {kind: base|renew|seat}
  - Acceptance: роут считает сумму (base=2300, renew=2300+200*extra, seat=прорация `200*days_left/30`), создаёт Payment с `sale_mode="corp"` + snapshot `{kind, group_id}`, возвращает payment URL провайдера; доступен только group-admin (для renew/seat) или юзеру без группы (для base)
  - Verify: юнит-тесты математики, ручной POST через кабинетную сессию
  - Files: `shop/backend/bot/app/web/webapp/corp_billing.py`, правки `billing_payments.py`/`payloads.py` под corp-create, `routes.py`

- [ ] Task: Corp-фулфилмент в `independent_success`
  - Acceptance: `is_corp_sale(sale_mode)` -> `resolve_corp_payment`: base -> создать группу+слоты+admin-seat; renew -> period_end+30d всем (panel expire sync); seat -> +1 extra-слот. Идемпотентно при повторном вебхуке (по payment.status)
  - Verify: юнит-тест finalize на каждый kind; E2E оплаты в dev-режиме локально
  - Files: `shop/backend/bot/payment_providers/shared/corp_success.py`, `independent_success.py`, `subscription_gifts.py`-подобный `is_corp_sale` в подходящем модуле

- [ ] Task: Тарифная запись `corp` в каталоге + сид
  - Acceptance: `infra/seed/tariffs.json` содержит `corp` (billing_model period, 30d=2300, кастом-поля цен/слотов); корп-тариф не отображается как обычная розничная карточка
  - Verify: `docker compose ... up` с сидом - каталог в админке грузится
  - Files: `infra/seed/tariffs.json`, при необходимости `tariffs_config.py` кастом-поля

## Блок D - инвайты и бот

- [ ] Task: Диплинк `?start=corp_<token>` + `join_corp_from_start`
  - Acceptance: regexp `^corp_([A-Za-z0-9_-]{8,64})$` в start_flow; валидный токен + свободный слот -> занятие + provisioning + welcome-экран; нет слота/протух -> понятное сообщение
  - Verify: E2E локально вторым TG-юзером; тест хендлера
  - Files: `shop/backend/bot/handlers/user/corp.py`, `start_flow.py` (точечно), `handlers/user/__init__.py`

- [ ] Task: Username- и e-mail-инвайты (pending)
  - Acceptance: инвайт по username - pending-запись + DM с кнопкой если юзер reachable, иначе персональная ссылка админу; авто-принятие при `/start`. Инвайт на e-mail - письмо со ссылкой на `app.<domain>/corp/join?token=...` (SMTP-цепочка gift-механики), принятие после логина в кабинете; отзыв инвайта
  - Verify: тесты матчинга username + e-mail-отправки + ручной прогон
  - Files: `shop/backend/bot/services/corp_invites.py`, `gift_email`-переиспользование, правки `start_flow.py`, тест

- [ ] Task: DM-уведомления корп-событий
  - Acceptance: шаблоны ru/en `corp_*` на события: приглашение, принятие (админу+участнику), disable/enable, смена квоты, удаление, продление, истечение; дедуп/политика уведомлений соблюдены
  - Verify: тесты отправки, прогон локали
  - Files: `shop/backend/bot/services/corp_notifications.py`, `locales/ru.json`, `locales/en.json`

## Блок E - webapp API

- [ ] Task: Роуты `/api/corp/*` для админа группы
  - Acceptance: `GET /api/corp/group` (сводка: слоты, period_end, цена продления, общая ставка), `GET /api/corp/members` (с метриками: расход сегодня vs квота, onlineAt/last_connected, lifetime), `POST /api/corp/members/{id}/quota|access`, `DELETE /api/corp/members/{id}`, `POST /api/corp/seats` (докупка->checkout), `DELETE /api/corp/seats/{id}`, `POST /api/corp/invites` (link|username|email), `DELETE /api/corp/invites/{id}`, `PATCH /api/corp/group` (имя, общая ставка, применить-ко-всем). Все 403 для не-админа группы
  - Verify: pytest webapp-роутов + ручной прогон через кабинет
  - Files: `shop/backend/bot/app/web/webapp/corp.py`, `corp_contracts.py`, `routes.py`

- [ ] Task: Корп-состояние в `/api/me` + блокировка покупок участника
  - Acceptance: `/api/me` отдаёт `corp: {role, group_name, quota_gb, access_disabled, pending_member}`; checkout-роуты отклоняют покупки/промокоды участника группы
  - Verify: тест сериалайзера + тест блокировки чекаута
  - Files: `webapp/serializers.py`/`account`-сериалайзеры, `billing*` проверки, тест

## Блок F - кабинет

- [ ] Task: BFF-прокси `cabinet/server/api/corp/[...].ts`
  - Acceptance: проксирует `/api/corp/*` с сессией, как `admin/[...].ts`
  - Verify: ручной запрос через кабинет
  - Files: `cabinet/server/api/corp/[...].ts`

- [ ] Task: Страница `cabinet/pages/corp.vue` + компоненты
  - Acceptance: раздел виден только group-admin; список участников (username, квота, расход сегодня vs квота, онлайн/последнее подключение, статус), тогл доступа, правка квоты и общей ставки (+применить ко всем), удаление, слоты-счётчик, докупка/удаление extra, инвайты (ссылка/username/e-mail), карточка биллинга с продлением; desktop+mobile в стиле кабинета
  - Verify: `npx nuxi typecheck`, ручной прогон, скрин-проверка
  - Files: `cabinet/pages/corp.vue`, `cabinet/components/corp/*`, правки навигации

- [ ] Task: Карточка участника + заглушка покупок
  - Acceptance: у участника в overview - корп-бейдж, остаток квоты сегодня, дата period_end, статус disable; `purchases.vue` для участника - заглушка "доступ от организации"
  - Verify: typecheck + ручной прогон двумя юзерами
  - Files: `cabinet/pages/index.vue`/`purchases.vue`, компоненты overview

## Блок G - финал

- [ ] Task: Локали, openapi-реген, gate-прогон
  - Acceptance: все новые ключи в ru.json+en.json; `openapi.json`/`openapi.generated.ts` регенерированы генератором; `pytest`, `ruff check backend`, `mypy backend`, `npm run check` (shop frontend если трогали), `npx nuxi typecheck` (cabinet) - зелёные
  - Verify: полный gate-прогон
  - Files: locales, сгенерированные артефакты

- [ ] Task: Выкат на сервер (по правилам AGENTS.md)
  - Acceptance: миграции применены, `tariffs.json` в volume обновлён (corp-запись), контейнеры пересобраны, health/логи чистые, E2E на проде наблюдением
  - Verify: docker ps/logs + живой сценарий покупки/инвайта
  - Files: `infra/minishop.prod.compose.yml` окружение при необходимости
