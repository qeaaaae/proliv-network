# ProlivVPN - подключение minishop к панели Remnawave

Пошаговая инструкция: от получения API-токена до рабочих подписок/триала/устройств.
Деплой VPS и нод - см. `infra/vps-setup.md`, спека - `SPEC.md`.

## 0. Текущее состояние стенда (снято 2026-10-26)

Проверено по живым контейнерам и БД панели:

- Панель: `remnawave/backend:3`, версия **3.4.7**, `http://remnawave:3000` в `remnawave-network`.
  UI для браузера - только через devproxy `http://localhost:3443` (см. п.2).
- `shop/.env`: `PANEL_API_URL=http://remnawave:3000/api` (ок), `PANEL_API_KEY=` **пусто**,
  `PANEL_WEBHOOK_SECRET=` пусто -> все запросы к панели отвечают `401 Unauthorized`.
- В БД панели: `api_tokens` пустая (токена нет вообще), internal squad только
  `Default-Squad` (`7dbe7d4e-ed7c-4e37-be69-4fac1739fc8f`, привязан inbound
  `Shadowsocks` из `Default-Profile`), external squads = 0, nodes = 0, hosts = 0.
- Встроенный subscription page config панели существует: `Default`,
  uuid `00000000-0000-0000-0000-000000000000`.
- Панельные env (`proliv.env`): `WEBHOOK_ENABLED=false`, `WEBHOOK_URL` пустой,
  `WEBHOOK_SECRET_HEADER` задан (64 символа), `SUBPAGE_API_TOKEN=change_me`,
  `SUB_PUBLIC_DOMAIN=localhost:3010`.
- Контейнер `remnawave-subscription-page` не поднят (profile `subpage`), порт 3010/3444 -> 502.

## 1. Как устроено подключение

- **minishop -> панель:** backend и worker ходят по `PANEL_API_URL` с заголовком
  `Authorization: Bearer <PANEL_API_KEY>` и принудительным `X-Forwarded-Proto: https`
  (`shop/backend/bot/services/panel_api_core.py::_prepare_headers`). Панель без
  proxy-заголовков рвёт соединение (`ProxyCheckMiddleware`, "Reverse proxy and HTTPS
  are required") - прямой `curl http://localhost:3000/...` без них вернёт пустой ответ,
  это нормально.
- **панель -> minishop (вебхуки):** панель шлёт `POST <WEBHOOK_URL>` с заголовком
  `X-Remnawave-Signature = hex(HMAC-SHA256(secret, body))`. Minishop сверяет его с
  `PANEL_WEBHOOK_SECRET` на роуте `POST /webhook/panel` (webhook-порт :8080 внутри
  контейнера). Пустой `PANEL_WEBHOOK_SECRET` = вебхуки всегда 401.
- **Ссылки подписки:** `SUBSCRIPTION_LINK_MODE=panel` (дефолт) - выдаётся
  `subscriptionUrl` панели (хост из `SUB_PUBLIC_DOMAIN` панели). Режим `minishop`
  выдаёт `SUBSCRIPTION_MINI_APP_URL + /s/<token>` - minishop сам проксирует
  `PANEL_API_URL/api/sub/<shortUuid>` и рендерит страницу инструкций.
- **Страница инструкций (guides):** при `SUBSCRIPTION_PAGE_CONFIG_PANEL_ENABLED=True`
  (дефолт) minishop тянет `GET /api/subscription-page-configs`, берёт конфиг по умолчанию
  (uuid `00000000-0000-0000-0000-000000000000`) и кеширует на 5 минут. Ошибка
  `subscription page config 00000000-... is unavailable` в логах - почти всегда
  следствие 401 на API, а не отсутствия конфига (конфиг в панели есть).

## 2. Шаг 1 - создать API-токен в панели

### Вариант A - через UI (рекомендуется)

1. Открыть `http://localhost:3443` (devproxy проставляет `X-Forwarded-Proto: https`;
   напрямую `http://localhost:3000` панель браузеру не отдаст).
2. Залогиниться админом (учётка `super`). Если пароль утерян -
   `docker exec -it remnawave cli` (Rescue CLI: сброс пароля/2FA админа).
3. В боковом меню: **Remnawave Settings** -> карточка **API Tokens** -> **Create**.
   - `name`: `minishop` (2-30 символов).
   - `expiresInDays`: поставить с запасом (например 3650) - протухший токен = тот же 401.
   - `scopes`: выбрать **все** (пресет `*`). Если хочется минимум - нужны ресурсы:
     `users` (read/write/actions/delete), `internal-squads` (read + bulk add/remove users),
     `external-squads` (read), `hosts` (read), `nodes` (read + restart), `system`
     (metadata/stats), `bandwidth-stats`, `hwid` (devices read/delete/stats),
     `subscription-page-configs`/`subscriptions` (read), `connections` (drop).
     Точные имена скоупов видны в модалке создания или через
     `GET /api/tokens/scopes` (только под admin JWT). Проще всего `*` -
     minishop делает и чтение, и мутации пользователей.
4. Токен показывается **один раз** - скопировать сразу.

### Вариант B - через API (если UI не под рукой, но есть пароль админа)

```powershell
# 1. Логин -> accessToken (JWT)
$login = curl.exe -s -X POST http://localhost:3443/api/auth/login `
  -H "Content-Type: application/json" `
  -d '{\"username\":\"super\",\"password\":\"<ПАРОЛЬ>\"}' | ConvertFrom-Json
$jwt = $login.response.accessToken   # или .access_token - смотря что вернёт

# 2. Создать токен (полный доступ, 10 лет)
$tok = curl.exe -s -X POST http://localhost:3443/api/tokens/ `
  -H "Authorization: Bearer $jwt" -H "Content-Type: application/json" `
  -d '{\"name\":\"minishop\",\"expiresInDays\":3650,\"scopes\":[\"*\"]}' | ConvertFrom-Json
$tok.response.token   # <-- это и есть PANEL_API_KEY
```

## 3. Шаг 2 - заполнить `shop/.env`

Править файл вручную (агент `.env` не трогает). Вот строки:

```dotenv
# уже есть и корректно:
PANEL_API_URL=http://remnawave:3000/api

# вставить токен из шага 2:
PANEL_API_KEY=<JWT_токен_из_панели>

# адрес панели для ссылок из админки в браузер (опционально):
PANEL_PUBLIC_URL=http://localhost:3443

# секрет вебхуков панели = WEBHOOK_SECRET_HEADER из proliv.env (см. шаг 4):
PANEL_WEBHOOK_SECRET=<скопировать значение WEBHOOK_SECRET_HEADER из proliv.env>

# сквад по умолчанию для новых юзеров панели (пока один - Default-Squad):
USER_SQUAD_UUIDS=7dbe7d4e-ed7c-4e37-be69-4fac1739fc8f
# когда появятся сквады по локациям - перечислить через запятую или разнести по тарифам:
# USER_SQUAD_UUIDS=<uk-squad-uuid>,<ee-squad-uuid>,<de-squad-uuid>

# внешний сквад (шаблоны подписочной страницы) - опционально, пока их нет:
# USER_EXTERNAL_SQUAD_UUID=

# ВАЖНО: overlay infra/minishop.compose.yml ставит backend APP_RUNTIME_MODE=dev,
# а PANEL_WRITE_MODE=auto в dev = DRY-RUN: запросы в панель только валидируются,
# пользователи в панели НЕ создаются. Для реальной записи в панель:
PANEL_WRITE_MODE=live
```

Заметки:

- `PANEL_API_URL` обязан оканчиваться на `/api` (контракт minishop; `/api` без
  завершающего слеша нормализуется кодом).
- `USER_SQUAD_UUIDS` - это fallback "по умолчанию" для создания юзера панели
  (`activeInternalSquads` в `POST /api/users`). Основной механизм - сквады на тарифах
  (`squad_uuids` в каталоге тарифов, админка -> Тарифы). Если тарифные сквады заданы,
  `USER_SQUAD_UUIDS` для покупок не нужен, но для триала/legacy-путей пригодится.
- `TRIAL_SQUAD_UUIDS`/`TRIAL_PREMIUM_SQUAD_UUIDS` - сквады триала; пусто = fallback на
  `USER_SQUAD_UUIDS`. Триал у нас выключен по спеке, можно не задавать.
- `PANEL_API_COOKIE` - не нужен (это для панелей за eGames reverse-proxy).
- Почти все `PANEL_*` потом можно поменять без рестарта в админке:
  **Admin -> System -> Settings -> Remnawave Panel**.

## 4. Шаг 3 - сквады и ноды для UK/EE/DE

Minishop к нодам напрямую не привязывается - никаких env про ноды нет и не нужно.
Вся привязка живёт в панели: `нода <- inbound конфиг-профиля <- internal squad <- юзер`.
Порядок зависимостей - снизу вверх, поэтому **сначала ноды, потом сквады**:

1. **Nodes -> Management -> Add node.** На каждом VPS ставится `remnawave/node`
   (агент), панель выдаёт `SECRET_KEY` для подключения ноды. При создании ноды
   выбирается конфиг-профиль и inbound, который нода будет обслуживать.
   Для 3 локаций - 3 ноды (UK, EE, DE).
2. **Config Profiles.** Сейчас есть только `Default-Profile` с одним inbound
   `Shadowsocks`. Под CDN-схему из SPEC (VLESS+WS+TLS на `uk./ee./de.<domain>`)
   потребуются свои inbounds - по одному на локацию или общий; каждый inbound
   привязывается к своей ноде.
3. **Hosts.** Точки входа, которые видит юзер в конфиге (домен/порт/путь):
   `uk.<domain>`, `ee.<domain>`, `de.<domain>` - по хосту на локацию, каждый
   привязан к своему inbound.
4. **Internal Squads.** **Management -> Internal Squads -> Create.** Два рабочих
   варианта:
   - один сквад `Main` со всеми inbounds (юзер получает все 3 локации сразу) -
     его uuid и идёт в `USER_SQUAD_UUIDS` / тарифы;
   - три сквада `UK`, `Estonia`, `Germany` - если тарифы должны различать локации
     (тогда uuid каждого сквада раскладывается по `squad_uuids` тарифов в админке).
   UUID сквада виден в UI (карточка/URL страницы сквада) или через API:
   `curl.exe -H "Authorization: Bearer <KEY>" http://localhost:3443/api/internal-squads`.
5. **External Squads** (опционально): **Management -> External Squads -> Create** -
   управляет тем, какой subscription page config/шаблоны получает юзер на
   подписочной странице. Сейчас их 0; если не создавать - все получают встроенный
   конфиг `Default`. Когда создадите - его uuid в `USER_EXTERNAL_SQUAD_UUID`.

Быстрый вариант "чтобы работало уже сейчас" без нод: `USER_SQUAD_UUIDS` уже можно
указать на существующий `Default-Squad` - панель примет создание юзера, но реальный
конфиг появится только когда сквад покрывает inbound с живой нодой.

## 5. Шаг 4 - вебхуки панели (истечение подписок, уведомления)

Без этого всё работает, но minishop не узнаёт о событиях панели (`user.expires_in_*`,
`user.expired`, hwid-события). Для локалки:

- в `proliv.env` панели:
  ```dotenv
  WEBHOOK_ENABLED=true
  WEBHOOK_URL=http://remnawave-minishop-backend:8080/webhook/panel
  WEBHOOK_SECRET_HEADER=<тот же секрет, что PANEL_WEBHOOK_SECRET в shop/.env>
  ```
  `http://` внутри docker-сети разрешён (3.x), `WEBHOOK_SECRET_HEADER` - строго
  64 символа a-zA-Z0-9; текущее значение уже сгенерировано - просто скопируйте его
  в `PANEL_WEBHOOK_SECRET` в `shop/.env`.
- в `shop/.env` выровнять базу для отображения в админке:
  `WEBHOOK_BASE_URL=http://remnawave-minishop-backend:8080`
  (для прода это будет публичный HTTPS `https://app.<domain>` + прокси на backend:8080).
- пересоздать панель: `docker compose --env-file proliv.env up -d remnawave`
  (recreate контейнера панели, БД не трогаем).

## 6. Применить и проверить

```powershell
# пересоздать backend и worker с новым env (env_file требует recreate):
docker compose -f shop/docker-compose.yml -f infra/minishop.compose.yml --env-file shop/.env up -d backend worker

# проверка токена с хоста (через devproxy):
curl.exe -H "Authorization: Bearer <PANEL_API_KEY>" http://localhost:3443/api/system/stats
# 200 + JSON = связь и токен ок; 401 = токен плохой/протух; 000/пусто = не та схема (см. прокси-заголовки)

# та же проверка с прямого порта панели - обязателен proxy-заголовок:
curl.exe -H "Authorization: Bearer <PANEL_API_KEY>" -H "X-Forwarded-Proto: https" http://127.0.0.1:3000/api/system/metadata

# изнутри backend-контейнера (как ходит сам minishop):
docker exec remnawave-minishop-backend sh -c 'wget -qO- --header="Authorization: Bearer $PANEL_API_KEY" --header="X-Forwarded-Proto: https" http://remnawave:3000/api/system/metadata'

# логи - ждём строку детекта версии:
docker logs remnawave-minishop-backend --since 10m | Select-String "Detected Remnawave panel version"
# Detected Remnawave panel version 3.4.7 generation=rw3-numeric-user-id support=unverified
```

Финальная проверка - админка minishop: **Admin -> Configuration issues / Проблемы
конфигурации**. Должны исчезнуть `panel_api_not_configured` / `panel_api_unreachable`;
может остаться warning `panel_api_version_unverified` - версия 3.4.7 новее
сертифицированной матрицы (<=3.4.5), это предупреждение, мутации не блокируются.

## 7. Типичные ошибки

| Симптом | Причина | Что делать |
|---|---|---|
| `401 Unauthorized` на всех вызовах панели | `PANEL_API_KEY` пуст/невалиден/протух | шаг 2 -> вставить токен, recreate backend/worker |
| Пустой ответ / `curl` виснет на `:3000` | нет `X-Forwarded-Proto: https` (ProxyCheckMiddleware) | ходить через `:3443` (devproxy) или добавить заголовок; minishop сам его шлёт |
| `subscription page config 00000000-...-000000000000 is unavailable` | почти всегда следствие 401 - конфиг есть, но `GET /api/subscription-page-configs/<uuid>` не прошёл | чинить токен; если и после - проверить, что скоуп токена покрывает subscription-page-configs |
| Юзер создаётся в minishop, но в панели его нет | `PANEL_WRITE_MODE=auto` + `APP_RUNTIME_MODE=dev` = dry-run | `PANEL_WRITE_MODE=live` в `shop/.env` |
| Вебхук панели -> 401 в логах backend | `PANEL_WEBHOOK_SECRET` != `WEBHOOK_SECRET_HEADER` панели | выровнять значения, recreate backend |
| Ссылка подписки ведёт на `localhost:3010` и не открывается | `SUBSCRIPTION_LINK_MODE=panel`, а `SUB_PUBLIC_DOMAIN=localhost:3010` и контейнер subpage выключен | локально: `SUBSCRIPTION_LINK_MODE=minishop` в `shop/.env` (шлюз `/s/` сам отдаст конфиг); либо поднять profile `subpage` + реальный `SUBPAGE_API_TOKEN` |
| `panel_api_version_unverified` в админке | 3.4.7 новее сертифицированной матрицы minishop | warning, не блокер; мутации идут best-effort |

Про `SUBPAGE_API_TOKEN`: контейнер `remnawave-subscription-page` (profile `subpage`,
порт 3010 -> devproxy `:3444`) нужен только если подписочную страницу должен отдавать
сам Remnawave. Он берёт `REMNAWAVE_API_TOKEN=${SUBPAGE_API_TOKEN}` - отдельный токен
панели (тот же UI: Remnawave Settings -> API Tokens; можно один общий токен на
minishop+subpage, либо узкий со скоупами metadata/subscriptions/subpage read).

## 8. Прод-чеклист

| Переменная | Прод-значение |
|---|---|
| `PANEL_API_URL` | `https://panel.<domain>/api` |
| `PANEL_PUBLIC_URL` | `https://panel.<domain>` |
| `PANEL_API_KEY` | отдельный прод-токен; можно сузить скоупы под список п.2 |
| `WEBHOOK_BASE_URL` | `https://app.<domain>` (прокси -> backend:8080) |
| `PANEL_WEBHOOK_SECRET` | = `WEBHOOK_SECRET_HEADER` прод-панели (64 hex) |
| `PANEL_WRITE_MODE` | не задавать: `APP_RUNTIME_MODE=production` -> live автоматически |
| `SUBSCRIPTION_LINK_MODE` | `minishop` (шлюз `/s/`) или `panel` + поднятая subpage на `sub.<domain>` |
| `SUB_PUBLIC_DOMAIN` (панель) | `sub.<domain>` |

## 9. Карта env-переменных (сводка)

| Переменная | Где | Что | Откуда взять |
|---|---|---|---|
| `PANEL_API_URL` | shop/.env | URL API панели, обязательно с `/api` | `http://remnawave:3000/api` (общая docker-сеть) / `https://panel.<domain>/api` |
| `PANEL_API_KEY` | shop/.env | Bearer-токен панели | панель: Remnawave Settings -> API Tokens -> Create |
| `PANEL_PUBLIC_URL` | shop/.env | панель для браузера админа | `http://localhost:3443` / `https://panel.<domain>` |
| `PANEL_WEBHOOK_SECRET` | shop/.env | секрет подписи вебхуков панели | = `WEBHOOK_SECRET_HEADER` из proliv.env |
| `PANEL_API_COOKIE` | shop/.env | cookie для eGames-прокси | не нужен локально |
| `PANEL_WRITE_MODE` | shop/.env | `auto`/`live`/`dry_run` | `live` для локалки (dev-runtime = dry-run!) |
| `PANEL_DRY_RUN_*` | shop/.env | поведение dry-run | дефолты ок |
| `USER_SQUAD_UUIDS` | shop/.env | internal squads для новых юзеров | uuid из Internal Squads панели / `GET /api/internal-squads` |
| `USER_EXTERNAL_SQUAD_UUID` | shop/.env | external squad для новых юзеров | uuid из External Squads; опционально |
| `TRIAL_SQUAD_UUIDS` | shop/.env | сквады триала | опционально; триал выключен |
| `SUBSCRIPTION_PAGE_CONFIG_PANEL_ENABLED` | shop/.env | читать guides-конфиг из панели | дефолт `True`, не трогать |
| `SUBSCRIPTION_PAGE_CONFIG_PATH/JSON*` | shop/.env/админка | локальный fallback конфига guides | только если панель недоступна |
| `WEBHOOK_BASE_URL` | shop/.env | база всех webhook-URL | `http://remnawave-minishop-backend:8080` локально |
| `WEBHOOK_ENABLED/URL/SECRET_HEADER` | proliv.env (панель) | доставка вебхуков minishop | см. шаг 5 |
| `SUBPAGE_API_TOKEN` | proliv.env | токен для remnawave-subscription-page | второй токен из панели (только если поднимать profile `subpage`) |
| `SUB_PUBLIC_DOMAIN` | proliv.env | хост в `subscriptionUrl` | `localhost:3010` / `sub.<domain>` |
