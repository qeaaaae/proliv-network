# Ops Runbook - типовые действия с панелью и нодами

Шпаргалка для рутинных операций. Всё через SSH с локальной машины, без UI.
Глубокие механики API - в `remnawave-api.md`, при инцидентах - `node-triage.md`.

## Доступы (где что лежит, без значений)

| Что | Где |
|---|---|
| SSH ко всем хостам | алиасы в `~/.ssh/config`, ключ `~/.ssh/proliv` |
| Panel API base | `http://localhost:3443/api` **с proliv-main** (не снаружи) |
| Panel API key | `PANEL_API_KEY` в `/opt/proliv/shop/.env` на main |
| Panel JWT (для UI-эндпоинтов) | `/root/.panel-jwt` на main |
| Shop DB | postgres-контейнер `remnawave-minishop-postgres`, db/user `remnawave_minishop` |
| Panel DB | контейнер `remnawave` -> postgres, база панели |

SSH-алиасы: `proliv-main`, `proliv-node-de`, `proliv-node-ee`, `proliv-node-fi`,
`proliv-node-uk`, `proliv-node-nl`, `proliv-node-kz`. RF - CDN-релей, не нода.

## 1. Проверка здоровья всех нод (30 секунд)

```bash
ssh proliv-main 'KEY=$(grep ^PANEL_API_KEY= /opt/proliv/shop/.env | cut -d= -f2- | tr -d "\"'"'"' \r"); \
  curl -s -H "Authorization: Bearer $KEY" http://localhost:3443/api/nodes' \
  | python3 -c "import json,sys; [print(n['name'],'conn:',n['isConnected'],'dis:',n['isDisabled']) for n in json.load(sys.stdin)['response']]"
```

`isConnected: false` -> идём в `node-triage.md`. `isDisabled: true` -> нода
выключена сознательно, не трогаем.

На хосте ноды:

```bash
ssh <node> "docker ps --format '{{.Names}} {{.Status}}'; uptime; df -h / | tail -1"
```

Ожидаемо: `remnanode Up`, иногда `remnanode-lte` (вторая нода на том же VPS).

## 2. Типовые действия

### Перезапуск ноды / форс-синк конфига

Отдельного sync endpoint нет - remnanode сам поллит панель (~1 мин).
Форс:

```bash
ssh <node> "docker restart remnanode"   # и remnanode-lte если есть
```

### Обновить конфиг профиля (маршрутизация и т.п.)

Полный рецепт в `remnawave-api.md` -> «Обновить config профиля».
Коротко: `GET /api/config-profiles` -> правишь `config` ->
`PATCH /api/config-profiles` с `{"uuid","config"}` целиком.
После PATCH ноды подхватят на следующем poll (~1 мин) или `docker restart remnanode`.

### Назначить профиль ноде / squad

`PATCH /api/nodes` с uuid в теле (НЕ `/api/nodes/{uuid}` - 404).
Squad: `PATCH /api/internal-squads` с полным списком inbound UUID.
Без squad юзеры не проходят: `invalid request user id`.

### Node plugins (Torrent Blocker)

Рецепт в `remnawave-api.md`. Снят только с NL; на DE/EE/FI (+LTE) активен.
Проверить баны: `ssh <node> "docker logs remnanode --since 24h | grep TORRENT"`.

### Проверить, что юзеры доехали до ноды

```bash
ssh <node> "docker logs remnanode --since 10m | grep -E 'users|XTLS'"
```

Строка `· N users` в логе = инбаунды в squad. 0 users = проблема squad.

### Логи ноды

```bash
ssh <node> "docker logs remnanode --since 1h"          # node service: config push, plugin events
ssh <node> "docker logs remnanode --tail 100"          # без фильтра
```

Xray access-лог внутри контейнера если включён - смотреть
`/usr/local/etc/xray/` в контейнере. Подробности - `remnawave-api.md` -> SSH.

### WARP-стек на ноде (DE/EE/FI/NL)

```bash
ssh <node> "systemctl status warp-svc warp-v4-shim warp-socks-forward --no-pager | grep -E '●|Active'"
```

Локальный socks-шим `127.0.0.1:40001`, прокси `127.0.0.1:40000`.
Проверка exit IP: `curl -x socks5h://127.0.0.1:40001 ifconfig.me`.
НЕ использовать WARP для Google/Gemini - Google метит его гео как RU/IR
(подробно `warp-ai.md`).

### LTE-ноды

Живут вторым контейнером `remnanode-lte` на VPS родителя (DE/EE/FI).
WARP не ставить - ходят через `172.17.0.1:40001` хоста.
Подробно `lte-vk.md`.

### Рестарт minishop (бот/воркер/backend)

Только с prod-оверлеем, из `/opt/proliv`:

```bash
ssh proliv-main "cd /opt/proliv && docker compose \
  -f shop/docker-compose.yml -f infra/minishop.compose.yml \
  -f infra/minishop.prod.compose.yml --env-file shop/.env --profile bot \
  up -d --build <backend|worker|bot|frontend>"
```

НИКОГДА без `minishop.prod.compose.yml` - dev-дефолты ломают PANEL_WRITE_MODE
(подписки слетают). `docker compose restart` не перечитывает env - после правки
`shop/.env` только `up -d`.

Миграции применяются сервисом `migrate` автоматически при `up -d`.

## 3. Данные и БД

- Активный giveaway: `docker exec remnawave-minishop-postgres psql -U remnawave_minishop -d remnawave_minishop -c "select giveaway_id,status,scheduled_draw_at from giveaways order by giveaway_id desc limit 5;"`
- Участники: таблица `giveaway_participants` (`user_id`, не `telegram_user_id`).
- Пользователи панели: `GET /api/users` (с пагинацией `start`/`size`).
- Миграции БД minishop append-only, последняя - `0114_giveaway_reminder`.

## 4. Бэкапы и cron (proliv-main)

| Что | Когда | Куда |
|---|---|---|
| `backup-tg.sh` | cron `0 0 * * *` | TG-архив panel.dump+shop.dump+configs, `/var/log/backup-tg.log` |
| `proliv-backup.timer` | 03:30 UTC | `/opt/proliv/backups` (14 дней) + rsync offsite на DE `/root/proliv-backups` |
| `rotate-hosts.py` | `17 */6 * * *` | ротация первой локации в подписке, `/var/log/rotate-hosts.log` |
| `proliv-cleanup.sh` | `30 4 * * 0` | еженедельная чистка, `/var/log/proliv-cleanup.log` |
| `referral_broadcast.py` | `20 9 * * *` | реф-рассылка юзерам с триалом/активной подпиской, троттл 14 дней/юзер, state `.referral_broadcast_state.json`, лог `/var/log/referral-broadcast.log` |

Скрипт ничего не хранит - дампы в `mktemp -d`, удаляются после отправки.

## 5. Гигиена серверов

Разобрано в `server-hygiene.md`. Коротко:
- `journalctl --vacuum` бесполезен без rotate: `journalctl --rotate && journalctl --vacuum-time=7d`
- apt-кэш: `apt-get clean`
- FI `xhttp_hdr.log` - logrotate настроен, не трогать руками
- `btmp`, snap-кэши - чистить по необходимости
- НЕ удалять `/root/*.bak`, `nginx_bak_*` - это точки отката

## 6. Чего НЕ делать без запроса

- Не открывать порты в ufw (ping DROP и NODE_PORT-only-from-panel - by design)
- Не править `destOverride`/bittorrent-правила в профилях
- Не снимать fail2ban/ping-drop
- Не трогать Default-Profile (UK/KZ) без причины
- Не править БД прода руками - только через миграции/код
- Не рестартовать remnanode «на всякий случай» - сначала triage

## Связанные доки

- `remnawave-api.md` - все API-операции с примерами
- `node-triage.md` - «не работает» decision tree
- `new-node.md` - создание ноды с нуля (7 этапов)
- `warp-ai.md` - маршрутизация YouTube/Gemini/AI, WARP
- `lte-vk.md` - LTE-хосты через VK/Яндекс CDN
- `hosts-subs.md` - хосты и подписки, rotate-hosts.py
- `server-hygiene.md` - диск/логи/кэши/бэкапы
- `torrent-block.md` - Remnawave Torrent Blocker plugin
