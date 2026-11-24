# Хосты и подписки Remnawave: как устроено и как править без UI

Всё через API с `proliv-main` — база и ключ см. `infra/remnawave-api.md`.
Никогда не править «по памяти» — сначала GET, потом PATCH полным
объектом.

## Модель: Panel → Profile → Inbound → Host → Subscription

```
Config Profile (xray-конфиг: inbounds+outbounds+routing)
   └── Inbound (VLESS-...-<CC>, uuid, порт, транспорт)
        └── Node (remnanode, activeConfigProfileUuid)
             └── Internal Squad (inbound uuids → юзеры)
Host (строка в подписке юзера)
   └── ссылается на inbound uuid + nodes + address/sni/host/extra
Subscription template (как JSON-конфиг собирается для клиента)
```

- **Node** — VPS с remnanode. Привязана к профилю через
  `PATCH /api/nodes {configProfile.activeConfigProfileUuid}`.
- **Inbound** — один листенер xray внутри профиля (Reality :443,
  WS :9443, XHTTP :9444/9445). Теги уникальны на ноду (`-<CC>`).
- **Host** — то, что видит юзер в списке локаций. Один host = одна
  строка подписки. Ссылается на конкретный inbound + конкретные ноды.
- **Squad** — список inbound uuid'ов, по которым панель раздаёт юзеров.
  Инбаунд вне squad = 0 юзеров = `invalid request user id`.

## Текущие хосты (GET /api/hosts, 21.11)

| remark | address:port | sni | host (CDN) | nodes |
|---|---|---|---|---|
| 🇬🇧 Великобритания | uk.proliv-network.xyz:443 | uk.proliv-network.xyz | — | UK-Node |
| 🇪🇪 Эстония | ee-2-src.proliv-network.xyz:443 | ee-2.proliv-network.xyz | — | EE2-Node-01 (163.245.52.213, qwins) |
| 🇪🇪 Эстония Резерв | ee-src.proliv-network.xyz:443 | ee.proliv-network.xyz | — | EE-Node-01 (31.76.70.98) |
| 🇳🇱 Нидерланды | nl.proliv-network.xyz:443 | nl.proliv-network.xyz | — | NL-Node |
| 🇩🇪 Германия | de-src.proliv-network.xyz:443 | de.proliv-network.xyz | — | DE-Node |
| 🇫🇮 Финляндия | fi-src.proliv-network.xyz:443 | fi.proliv-network.xyz | — | FI-Node |
| 🇰🇿 Казахстан | kz.proliv-network.xyz:443 | kz.proliv-network.xyz | — | KZ-Node |
| 🇪🇺 LTE - Основной | ee-2.proliv-network.xyz:443 | ee-2.proliv-network.xyz | ee-2.proliv-network.xyz | EE2-Node-LTE (VK CDN) |
| 🇪🇺 LTE - Основной 2 | fi.proliv-network.xyz:443 | fi.proliv-network.xyz | fi.proliv-network.xyz | FI-Node-LTE (VK CDN) |
| 🇪🇺 LTE - Резерв 1 | ee.proliv-network.xyz:443 | ee.proliv-network.xyz | ee.proliv-network.xyz | EE-Node-LTE (yccdn) |
| 🇪🇺 LTE - Резерв 2 | de.proliv-network.xyz:443 | de.proliv-network.xyz | de.proliv-network.xyz | DE-Node-LTE (yccdn) |

У прямых локаций `host` пустой (не CDN). У LTE `host` = front-домен —
edge шлёт его в Host-заголовке на origin.

## Поля host, которые надо понимать

| Поле | Что делает | Когда заполнять |
|---|---|---|
| `remark` | Имя в списке локаций клиента | Всегда, с флагом emoji |
| `address`+`port` | Куда клиент коннектится | IP или домен, куда смотрит клиент |
| `sni` | TLS SNI в Reality/TLS | Домен, который «притворяется» клиент |
| `host` | HTTP Host для WS/XHTTP за CDN | Только CDN-хосты (LTE) |
| `inbound` (uuid) | Какой inbound профильный конфиг юзать | uuid инбаунда из профиля |
| `nodes` | На каких нодах хост активен | uuid'ы нод; пусто = все? (см. API) |
| `xhttpExtraParams` | xhttp extra для клиента | Только xhttp-хосты, = inbound extra |
| `sockoptParams` | tcpFastOpen/tcpNoDelay клиента | REALITY-хосты (де/инцидент TG media) |
| `viewPosition` | Порядок в подписке | Управляется rotate-hosts.py |
| `isDisabled` | Выключить хост | Вместо удаления — клиент перестаёт видеть |

## API: чтение и правка хостов

```bash
ssh proliv-main
export KEY=$(awk -F= "/^PANEL_API_KEY=/{print \$2}" /opt/proliv/shop/.env | tr -d "\"\r")
B=http://localhost:3443/api

# все хосты
curl -s -H "Authorization: Bearer $KEY" $B/hosts | python3 -m json.tool > /tmp/hosts.json
# ответ: response.hosts[]

# правка ОДНОГО поля (остальное сохранить из GET!)
# берём объект целиком, меняем, шлём PATCH /api/hosts с uuid в теле
python3 - <<'PY'
import json,urllib.request,os
key=os.environ['KEY']
hosts=json.load(open('/tmp/hosts.json'))['response']['hosts']
h=[x for x in hosts if 'LTE - Основной' in x['remark']][0]
h['isDisabled']=True   # пример
req=urllib.request.Request('http://localhost:3443/api/hosts',
    data=json.dumps({'uuid':h['uuid'], **{k:h[k] for k in
      ['remark','address','port','sni','host','inbound','nodes','xhttpExtraParams','sockoptParams','viewPosition','isDisabled'] if k in h}}).encode(),
    headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'},method='PATCH')
print(urllib.request.urlopen(req).status)
PY
```

**Важно**: PATCH /api/hosts ждёт объект с `uuid` — массив и `/{uuid}`
не работают (404). Тело = поля host, не весь wrapper.

## Добавить хост для новой ноды/инбаунда (чеклист)

1. Инбаунд создан в профиле → `GET /api/config-profiles/inbounds`
   → записать его uuid.
2. Инбаунд добавлен в Default-Squad (иначе 0 юзеров).
3. `PATCH /api/hosts` — новый объект:
   - remark `🇽🇽 Страна`;
   - address/sni = `<cc>.proliv-network.xyz` (или `*-src.` дляReality);
   - host = front-домен только для CDN;
   - inbound = uuid из п.1;
   - nodes = [uuid ноды];
   - для xhttp: `xhttpExtraParams` = копия `xhttpSettings.extra`
     инбаунда (клиент и сервер должны совпадать!);
   - для xhttp за CDN также копировать ТРАНСПОРТНЫЕ поля с рабочего
     хоста: `securityLayer: "TLS"`, `fingerprint: "chrome"`,
     `alpn: ["h2","http/1.1"]`, `path` (со слешем на конце),
     `xhttpExtraParams.path: "/"`. Без них клиент падает с
     `failed to parse json config failed to build outbounding`
     (инцидент EE2-LTE 23.11);
   - для Reality: `sockoptParams` = `{"tcpFastOpen":true,"tcpNoDelay":true}`.
4. Проверка: `GET /api/sub/<shortUuid>` с UA клиента → новый хост в
   выдаче; реальное подключение → выход = IP ноды.

## Subscription template (клиентский routing)

Шаблон `Default` (XRAY_JSON, uuid `3a575487-4b1d-47da-901e-9e928254385a`)
содержит `templateJson.routing.rules` — правила, которые применяются
у клиента поверх серверного routing. Сейчас там (см. lan-freeze-fix.md):

```json
[
  {"type":"field","protocol":["quic"],"outboundTag":"block"},
  {"type":"field","protocol":["bittorrent"],"outboundTag":"direct"},
  {"type":"field","domain":["geosite:category-ru"],"outboundTag":"direct"},
  {"type":"field","ip":["geoip:private","224.0.0.0/4","255.255.255.255/32","ff00::/8"],"outboundTag":"direct"},
  {"type":"field","network":"tcp,udp","port":"135-139,445","outboundTag":"block"},
  {"type":"field","network":"tcp,udp","port":"1900,2869,3702,5353,5355,5357-5358","outboundTag":"block"}
]
```

- Happ прогоняет JSON 1:1 — правила шаблона действуют, правила приложения
  нет. Поэтому LAN-фриз-фикс сделан именно тут.
- `profile-update-interval: 6` часов — клиенты подтягивают новый шаблон
  сами, но можно дёрнуть refresh.
- PATCH: `PATCH /api/subscription-templates` с uuid+templateJson.

## Авто-ротация хостов

Cron на main: `17 */6 * * * /usr/bin/python3 /opt/proliv/rotate-hosts.py`
(лог `/var/log/rotate-hosts.log`).

**Отложенное скрытие хостов**: `/opt/proliv/infra/host-hide-schedule.py`,
cron `15 0 * * *` (03:15 MSK). Скрипт работает **по UUID хостов**
(переименования remark его не ломают) и по датам МСК проставляет
`isHidden=true` (хост исчезает из подписки, сам не удаляется):
- 2026-11-27: `🇪🇪 Эстония Резерв` (старая EE), `🇪🇺 LTE - Резерв 1`, `🇪🇺 LTE - Резерв 2`, `🇬🇧 Великобритания`
- 2026-11-29: `🇫🇮 Финляндия`, `🇪🇺 LTE - Основной 2` (FI)
- 2026-12-09: `🇰🇿 Казахстан`
Откат: `isHidden=false` через PATCH /api/hosts. Лог `/var/log/host-hide.log`.

Скрипт каждый запуск **ротирует ГРУППЫ локаций** (антифинг/балансировка
первой строки в подписке). Не трогает:
- хосты с `LTE` в remark и `Казахстан` (pinned);
- disabled/hidden-хосты.

Правила порядка (важно, проверено 23.11):
- **Резерв не может быть выше основной локации.** Хосты группируются по
  remark без суффикса ` Резерв`: `🇪🇪 Эстония` + `🇪🇪 Эстония Резерв` =
  одна группа, резерв всегда идёт сразу после основной и двигается
  вместе с ней при ротации.
- **LTE строго по номерам:** `LTE - Основной`, `LTE - Основной 2`,
  `LTE - Резерв 1`, `LTE - Резерв 2`. Скрипт каждый запуск пересортировывает
  LTE-хосты (основные по номеру, потом резервы по номеру) и раздаёт им
  позиции 8-11 - порядок не поплывёт даже после переименований.
- Переименования remark безопасны для hide-скрипта (он по UUID), но
  rotate-hosts.py группирует по remark - при смене схемы имён сверить
  `RESERVE_SUFFIX`/`PINNED_MARKERS` в скрипте.

JWT для API берёт из `/root/.panel-jwt` (HS256, APP_SECRET).

## Диагностика «хост не виден в подписке»

```bash
# 1. Хост есть и enabled?
curl -s -H "Authorization: Bearer $KEY" $B/hosts | python3 -c "
import json,sys; hs=json.load(sys.stdin)['response']['hosts']
[print(h['remark'],h['isDisabled'],h.get('nodes')) for h in hs]"

# 2. Инбаунд хоста в squad?
curl -s -H "Authorization: Bearer $KEY" $B/internal-squads | python3 -m json.tool

# 3. Нода онлайн и на нужном профиле?
curl -s -H "Authorization: Bearer $KEY" $B/nodes | python3 -m json.tool | grep -E 'name|isConnected|activeConfig'

# 4. Сама подписка отдаёт?
curl -s -A 'Happ' 'https://<sub-domain>/api/sub/<shortUuid>' | head -c 500

# 5. yml/base64 подписки: remark должен присутствовать в raw выдаче.
```

Типовые причины: `isDisabled`, инбаунд не в squad, нода offline,
`viewPosition`/`isHidden` флаги, у юзера устаревшая подписка.

## Чего не делать

- Не создавать хост «вручную через UI» — только API, чтобы был
  воспроизводимый след.
- Не менять `inbound` uuid на чужой профиль — клиент получит конфиг,
  который нода не слушает.
- Не дублировать remark — клиент запутается.
- Не забывать `xhttpExtraParams` для xhttp-хостов — без него клиент
  шлёт дефолтные параметры, сервер их не поймёт (инцидент VK 12.11).
- Не создавать xhttp-хост с `securityLayer: DEFAULT` — клиентский
  outbound не собирается (`failed to build outbounding`). TLS-поля
  обязательны, см. чеклист выше.
- Не удалять хосты — `isDisabled: true` обратимо, удаление ломает
  существующие подписки.

## Связанные доки

- `infra/remnawave-api.md` — все endpoint'ы и форматы PATCH
- `infra/lan-freeze-fix.md` — клиентский routing шаблона
- `infra/lte-vk.md` — LTE-хосты и VK CDN
- `infra/new-node.md` — создание ноды (этапы 4-5: профиль+squad)
- `infra/node-triage.md` — «не работает» decision tree
- `infra/panel-setup.md` — первичная установка панели
- `infra/vps-setup.md` — VPS+DNS+deploy
