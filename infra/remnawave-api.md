# Remnawave Panel API - управление нодами/профилями без UI

Всё делается curl'ом с `proliv-main`. Браузер и UI не нужны.
Написано по факту работы 2026-11-17 (инцидент с NL-нодой).

## Доступ

```bash
ssh proliv-main
cd /opt/proliv
export KEY=$(awk -F= "/^PANEL_API_KEY=/{print \$2}" shop/.env | tr -d "\"\r")
BASE=http://localhost:3443/api
# все запросы: curl -s -H "Authorization: Bearer $KEY" $BASE/...
```

`PANEL_API_KEY` лежит в `shop/.env`, scope `api` в панели (full access).

## ВАЖНО: форма PATCH

Панель принимает **объект** `{"uuid": "...", ...поля}` в теле `PATCH /api/<resource>`.
НЕ работает: `PATCH /api/nodes/{uuid}` (404), массив в теле (400 "expected object"),
пустая строка вместо uuid (400 "invalid_format").

```bash
# узел
curl -X PATCH $BASE/nodes -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '{"uuid":"<node-uuid>","activePluginUuid":null}'

# профиль - конфиг целиком
curl -X PATCH $BASE/config-profiles -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '{"uuid":"<profile-uuid>","config":{...полный config...}}'

# squad - inbounds массив UUID, заменяет ПОЛНЫЙ набор
curl -X PATCH $BASE/internal-squads -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '{"uuid":"<squad-uuid>","inbounds":["<inbound-uuid>",...]}'
```

## Типовые операции

### Список нод и их профили

```bash
curl -s $BASE/nodes -H "Authorization: Bearer $KEY" | python3 -c "
import json,sys
d=json.load(sys.stdin); ns=d.get('response',d)
ns=ns.get('nodes',ns) if isinstance(ns,dict) else ns
for n in ns: print(n['name'],'|',n['configProfile']['activeConfigProfileUuid'],'|',n['isConnected'])"
```

### Назначить ноде профиль

```bash
curl -X PATCH $BASE/nodes ... -d '{
  "uuid":"<node-uuid>",
  "configProfile":{"activeConfigProfileUuid":"<profile-uuid>","activeInbounds":[]}
}'
```

`activeInbounds: []` = все инбаунды профиля. Нода подхватывает конфиг сама
(поллит панель, hash-check в логах). Форсировать:
`ssh <node-alias> docker restart remnanode` (~30 сек даунтайма ноды).

### Обновить config профиля

1. `GET $BASE/config-profiles` -> найти профиль по `name`, взять `uuid` и `config`.
2. Править `config` (inbounds/outbounds/routing).
3. `PATCH $BASE/config-profiles` с `{"uuid","config"}` - конфиг целиком.
4. Все ноды на профиле получают новый конфиг автоматически.

### Node plugins (Torrent Blocker и т.п.)

```bash
# создать плагин
curl -X POST $BASE/node-plugins -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '{"name":"torrent-blocker","pluginConfig":{"torrentBlocker":{"enabled":true,"blockDuration":3600}}}'

# привязать к ноде
curl -X PATCH $BASE/nodes ... -d '{"uuid":"<node>","activePluginUuid":"<plugin-uuid>"}'
# снять (null, НЕ пустая строка)
curl -X PATCH $BASE/nodes ... -d '{"uuid":"<node>","activePluginUuid":null}'
```

### КРИТИЧНО: squad membership

Инбаунд работает для юзеров ТОЛЬКО если он входит в internal squad.
Инбаунд вне squad = нода получает пустой список юзеров -> все клиенты
ловят `invalid request user id` в xray-логе. Симптом: «нода жива, порт
открыт, пинги идут, но никто не подключается».

```bash
# все инбаунды всех профилей + их squad
curl -s $BASE/config-profiles/inbounds -H "Authorization: Bearer $KEY" | python3 -c "
import json,sys
for i in json.load(sys.stdin)['response']['inbounds']:
    print(i['uuid'],'|',i['tag'],'|',i['profileUuid'],'| squads:',i['activeSquads'])"

# состав squad
curl -s $BASE/internal-squads -H "Authorization: Bearer $KEY"
```

При создании НОВОГО профиля обязательно добавить его инбаунды в squad
(сейчас все 16 в Default-Squad `2b5f5dcd-0099-4f51-bc26-0ba04c240d63`).

### Проверка что юзеры доехали до ноды

```bash
ssh <node-alias> "docker logs remnanode --since 10m | grep users"
# ищем строки вида: 'VLESS-TCP-Reality-NL-v2 · 16 users'
# Нет строки или '· 0 users' = инбаунд не в squad
```

## Что НЕ работает через API (проверено)

- `PATCH /api/nodes/{uuid}` -> 404 (только PATCH /api/nodes + uuid в теле)
- `PATCH /api/nodes` массивом -> 400; `activePluginUuid:""` -> 400
- `GET /api/inbounds` -> 404 (использовать /api/config-profiles/inbounds)
- `GET /api/squads` -> 404 (только /api/internal-squads)
- Отдельного sync/restart endpoint у нод нет - только `docker restart remnanode`
  на ноде или ждать hash-poll (~1 мин)

## Актуальное состояние (2026-11-17)

| Node | Profile | Profile UUID |
|------|---------|--------------|
| DE-Node-01 | DE-Profile | 451b8d6a-218c-4fc3-a1cf-04ca940e6548 |
| DE-Node-LTE | DE-LTE-Profile | 11a59109-ce23-46b1-ae7a-bbcbcb2b6b14 |
| EE-Node-01 | EE-Profile | 9110bb10-a34c-4e75-b3fc-f9e1c5cf4a57 |
| EE-Node-LTE | EE-LTE-Profile | 9381c9d1-5c85-4671-8f2f-f0ce7ab6c3ba |
| FI-Node-01 | FI-Profile | 9b29115f-ae59-43dd-92d1-09f9d24c38ba |
| FI-Node-LTE | FI-LTE-Profile | 268460a0-7d23-4d70-8785-95aadcf20530 |
| UK-Node-01 | Default-Profile | 00000000-0000-0000-0000-000000000000 |
| KZ-Node-01 | Default-Profile | 00000000-0000-0000-0000-000000000000 |
| NL-Node-01 | NL-Profile-v2 | 58c03fa0-3724-47ea-a045-47cf139b7f80 |

- Профили `NL-Profile` (4a270698) и `NL-Profile-v2` (58c03fa0) - кастомные,
  с `ai-via-warp` outbound (см. `infra/warp-ai.md`).
- Torrent Blocker plugin `8794c237-8543-4261-992f-fa3b5af495b8`
  (enabled, blockDuration 3600) привязан ко всем нодам КРОМЕ NL.
- Default-Squad: 16 инбаундов (все профили включая NL-v2).

## Диагностика типовых проблем

```bash
# нода connected но юзеры не проходят?
ssh <node> "docker exec remnanode tail -100 /var/log/xray/current | grep 'invalid request user id'"
# -> inbound не в squad: GET /api/config-profiles/inbounds -> activeSquads

# нода offline?
curl $BASE/nodes | python3 -c "...isConnected..."
ssh <node> "docker ps | grep remnanode; docker logs remnanode --tail 20"

# конфиг доехал?
ssh <node> "docker logs remnanode --since 10m | grep -E 'Config Hash|users'"

# плагин сломал ноду?
curl -X PATCH $BASE/nodes -d '{"uuid":"<node>","activePluginUuid":null}'
ssh <node> "docker restart remnanode"
```

## SSH к нодам и логи

```bash
# xray access-лог (внутри контейнера remnanode)
ssh proliv-node-nl "docker exec remnanode tail -50 /var/log/xray/current"

# docker-логи ноды (config push, errors)
ssh proliv-node-nl "docker logs remnanode --since 10m"
```

Алиасы: `proliv-node-de|uk|ee|fi|nl|kz|rf`, `proliv-main` - в `~/.ssh/config`.

## История: как всё разворачивалось

1. **Базовые профили** (Default/DE/EE/FI + LTE) - копии Default-Profile,
   правка `config` через PATCH /api/config-profiles. У каждого профиля
   свои теги инбаундов (`-DE`, `-EE`...), чтобы ноды не путали inbound'ы.

2. **yt-via-nl** - outbound `socks` на `87.58.201.121:8444` (python
   socks5-relay на NL: `/opt/socks-relay/socks5.py`, systemd
   `socks-relay.service`). UFW пускает только IP нод. Релей сам выбирает
   семейство: YouTube-family -> IPv4, остальное -> IPv6.

3. **ai-via-warp** - outbound `socks` на `127.0.0.1:40001` (warp-v4-shim)
   на DE/EE/FI и NL; на LTE-нодах `172.17.0.1:40001` (docker0 forward).

4. **NL-Profile-v2** - актуальный профиль NL-Node-01: YouTube ->
   yt-via-nl, `geosite:google`+gemini -> yt-via-nl (как в DE/EE/FI),
   non-Google AI (openrouter, claude, openai, anthropic, perplexity,
   mistral, x.ai, copilot) -> ai-via-warp. Важно: google НЕ должен
   попадать в ai-via-warp - WARP гео-помечен Google как RU/IR.

5. **Torrent Blocker** - node-plugin, включён на 8 нодах. На NL снят:
   `PluginService batch error: No such file or directory` (17.11).

6. **Squad** - Default-Squad `2b5f5dcd` = 16 инбаундов. Инцидент 17.11:
   NL-профили не были в squad -> NL отдавал 0 юзеров -> тотальный отказ.
   Лечение: PATCH /api/internal-squads с полным списком inbound UUIDs.

7. **Матрица Gemini/YouTube по всем нодам и история** - `infra/warp-ai.md`,
   секция «Полная матрица». Кратко: UK/KZ -> google DIRECT, все остальные
   -> yt-via-nl -> NL IPv6; YouTube везде -> NL IPv4; AI -> warp (кроме
   UK/KZ - у них direct).

## Связанные доки

- `infra/warp-ai.md` - WARP-эгресс для AI, NL-Profile-v2, yt-via-nl relay,
  полная матрица маршрутизации Gemini/YouTube/AI по всем нодам
- `infra/torrent-block.md` - Torrent Blocker plugin + инциденты
- `infra/new-node.md` - runbook создания новой ноды с нуля (7 этапов)
- `infra/cdn-xhttp.md` - CDN-инбаунды (WS/XHTTP :9443/:9444)
- `infra/lan-freeze-fix.md` - reject-правила private/SMB
- `infra/bot.md` - архитектура minishop
- `infra/panel-setup.md` - первоначальная установка панели
- `infra/node-triage.md` - decision tree «не работает» (пинг/SQUAD/юзеры)
- `infra/ops-runbook.md` - типовые операции: доступы, health-check, рестарты,
  бэкапы/cron, minishop deploy, «чего не делать»
- `infra/hosts-subs.md` - хосты и подписки: модель, PATCH /api/hosts, шаблон, ротация
