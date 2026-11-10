# CDN xhttp транспорт (LTE-хосты)

Рабочая схема на примере Эстонии. Цель: прятать VLESS-xhttp за публичный CDN,
чтобы мобильные операторы видели обычный HTTPS к медиа-домену.

## Факт на проде (обновлено 2026-11-10: каскад через РФ-релей)

```
клиент -> yccdn edge -> rf-src (RF :443, nginx stream ssl_preread)
       -> ee-src/de-src :443 REALITY -> nginx :8443 -> xhttp :9445
```

- **RF-нода `48.102.213.215` (serv.host, ssh `proliv-node-rf`)** - тупой
  TCP-релей, TLS НЕ терминирует, xray/remnanode нет, в панели не
  зарегистрирована. nginx stream на `:443` роутит по SNI
  (`/etc/nginx/stream-enabled/lte-cdn-relay.conf`): SNI=front-домен
  (`Заголовок Host` ресурса CDN) -> upstream `ee-src:443` или `de-src:443`.
- Оба CDN-ресурса (ee. + de.) смотрят в **одну** origin-группу `rf-src`
  -> `rf-src.proliv-network.xyz` (A -> 48.102.213.215, Cloud DNS).
  Старые группы `common-ee-src-*`/`common-de-src-*` неиспользуемы.
- На EU-нодах **ноль правок**: vhost'ы/серты/xhttp как были. Трафик от
  эджа приходит с IP РФ; в `xhttp_access.log` всё равно `127.0.0.1`
  (steal). Юзерские uuid доезжают до EU целиком - учёт на LTE-нодах
  панели не меняется.
- Харденинг РФ по эталону нод: ufw (443 + 80 + 22 limit + 40 сканер-банов),
  sshd key-only, ping off, bbr/fq/tfo. Backup-ключ панели добавлен
  (nodecheck).
- **Декой на РФ (2026-11-10):** сайт-маскировка ООО «СтанкоПрецизион»
  (ЧПУ-станки, 4 страницы, `/var/www/site`, сиды `infra/decoy-rf/`).
  `:80` default_server отдаёт сайт по любому имени/IP; SNI
  `rf-src.proliv-network.xyz` в stream-мапе -> `127.0.0.1:8443`
  (LE-серт webroot'ом через `:80`, certbot.timer на авто-renew).
  Чужой/пустой SNI на `:443` -> RST. Т.е. картинка хоста: русская
  контора с сайтом на 80/443 + TLS-бекенд у Яндекс-CDN.
- Проверка релея с самой РФ: `curl -sk --resolve ee.proliv-network.xyz:443:127.0.0.1
  https://ee.proliv-network.xyz/media/feed/preview/?sess_id=t` -> `400`.
  nodecheck.sh: секция "RF CDN relay" (nginx + оба upstream).

## Предыдущее состояние (сплит LTE на отдельные ноды, 2026-11-08)

- EE: `ee.` -> **Yandex CDN (yccdn)**, edge -> `ee-src:443` -> **xray REALITY self-steal**
  -> nginx `127.0.0.1:8443` -> xray xhttp `:9445`
  (контейнер `remnanode-lte`, нода `EE-Node-LTE`, cm=1.7).
  С 2026-11-09 схема = DE: `:443` отдан REALITY (`VLESS-TCP-Reality-EE-443`),
  хост `🇪🇪 Эстония` = `ee-src:443`; legacy `:10443` удалён в тот же день.
  С 2026-11-10 edge ходит через РФ-релей (см. выше), сама схема на ноде не менялась.
- DE: `de.` -> Yandex CDN (yccdn), edge -> `de-src:443` -> xray REALITY self-steal ->
  nginx `:8443` -> xray xhttp `:9445` (контейнер `remnanode-lte`, нода `DE-Node-LTE`, cm=1.7).
- LTE-трафик учитывается отдельно от обычного: у LTE-нод `consumptionMultiplier=1.7`
  (CDN-трафик платный), у базовых = 1.0. В remark - множитель без привязки к
  стране: с 2026-11-10 хосты называются `🇪🇺 x2 LTE доступ №1` (ee) и
  `🇪🇺 x2 LTE доступ №2` (de); ранее были `🇪🇪 2x LTE Эстония` /
  `🇩🇪 2x LTE Германия`.
- В подписке хосты выглядят как `VLESS·XHTTP·TLS·JSON` (Happ).

## LTE-ноды (вторая нода на том же VPS, 2026-11-08)

remnanode **запрещает две ноды в одном network namespace** (ошибка
"ANOTHER REMNAWAVE NODE IS ALREADY RUNNING"), поэтому второй контейнер
работает в bridge-режиме, а не host:

```
docker run -d --name remnanode-lte --restart always \
  -p 2223:2223 -p 127.0.0.1:9445:9445 \
  -e NODE_PORT=2223 -e "SECRET_KEY=$(cat /root/.remnanode-lte-key)" \
  remnawave/node:3.4.3
```

- `2223` опубликован наружу, UFW: только с `144.31.240.216` (panel->node).
- `9445` опубликован на `127.0.0.1` хоста - nginx проксирует туда вместо старого `:9444`.
- Из-за bridge инбаунд в профиле слушает `0.0.0.0` (внутри контейнера), не `127.0.0.1`.
- SECRET_KEY лежит в `/root/.remnanode-lte-key` на каждой ноде (600 root).
- Панель требует уникальный `address` ноды: у LTE-нод он = домен источника
  (`de-src.proliv-network.xyz` / `ee-src.proliv-network.xyz`), не IP.
- Накладные расходы замеренные: ~64 МБ RAM, ~0% CPU на контейнер.

Панель:

| сущность | DE | EE |
|----------|----|----|
| LTE-нода | `DE-Node-LTE` `d2e7022b-e64c-4f07-a6e8-f3539ce63065` (de-src:2223, cm 1.7) | `EE-Node-LTE` `9ff3cb93-49ef-4529-a2b7-1309f5f3f880` (ee-src:2223, cm 1.7) |
| профиль | `DE-LTE-Profile` `11a59109-ce23-46b1-ae7a-bbcbcb2b6b14` | `EE-LTE-Profile` `9381c9d1-5c85-4671-8f2f-f0ce7ab6c3ba` |
| xhttp inbound | `7cae8e70-e774-45cc-b244-945faeb990d7` `VLESS-XHTTP-CDN-DE-LTE` :9445 | `f0e3e463-577b-4b1d-a026-fb7aaeaadccb` `VLESS-XHTTP-CDN-EE-LTE` :9445 |

Базовые ноды `DE-Node-01`/`EE-Node-01`: старые xhttp-инбаунды
(`0b1a9300`/`2e302a60`) сняты с activeInbounds, `EE-Node-01` cm возвращён в 1.0.
Оба новых инбаунда добавлены в Default-Squad, старые из сквада убраны.
nginx на обеих нодах: `proxy_pass` `/media/feed/preview` и `/api/xhttp`
переключены `127.0.0.1:9444` -> `127.0.0.1:9445` (бэкапы `*.bak-9445` в
`/etc/nginx/sites-enabled/`).

## Топология

```
клиент -> edge CDN (ee.proliv-network.xyz:443, yccdn)
        -> nginx :443 на ноде (server_name ee.proliv-network.xyz / ee-src...)
        -> xray xhttp 127.0.0.1:9445 (с 2026-11-08; контейнер remnanode-lte)
        -> выход через IP ноды
```

REALITY на той же ноде вынесен с 443 на `10443`, потому что 443 занимает nginx.
В отличие от DE, REALITY-стейплинг для CDN-пути **не используем** - эдж ходит в
nginx :443 напрямую (как было и с CDNvideo), переделывать не стали.

**МИГРИРОВАНО 2026-11-09 (правило AGENTS.md #8):** публичный `:443` на EE теперь
REALITY (инбаунд `VLESS-TCP-Reality-EE-443` `f974d9d7-a384-4f98-8bb3-ae0683bcb5e2`,
клон старого 10443 с тем же privateKey/dest `127.0.0.1:8443`), nginx убран с
публичного :443 в `127.0.0.1:8443` (vhost'ы `proliv-tls`/`proliv-tls-src` приведены
к паритету: `/media/feed/preview`+`/api/xhttp` -> `:9445`, `/api/ws` -> `:9443`),
`proliv-cdn` и протухшие `*.bak-9445` (со старым `:9444`) убраны из sites-enabled
в `/root/`. Хост `🇪🇪 Эстония` = `ee-src:443`. Старый `VLESS-TCP-Reality-EE:10443`
**удалён в тот же день** (профиль/нода/сквад) - клиенты со старыми ссылками
получают `ee-src:443` после обновления подписки. Бэкапы:
`/root/ee-profile-pre443-backup.json`, `/root/ee-host-pre443-backup.json` на
proliv-main, `/root/proliv-tls*.bak-443mig` на EE.

**`ssl_reject_handshake` на `127.0.0.1:8443` - ВЕЗДЕ (6/6 нод):** файл
`proliv-tls-reject` (default_server). Чужой SNI через steal получает TLS-reset.
Для NL (Ubuntu 20.04) и KZ (22.04), где штатный nginx 1.18 не умел
`ssl_reject_handshake`, nginx обновлён с .deb из pool nginx.org: NL -> 1.28.0,
KZ -> 1.28.3 (`/root/nginx_bak_upg_*` - бэкапы /etc/nginx до апгрейда; пакет
перезаписал nginx.conf - восстановлен из бэкапа, иначе пропадает
`sites-enabled`). ssh на KZ: `proliv-node-kz` (79.183.193.149, ключ `~/.ssh/proliv`).
На KZ остался косметический warn `listen ... http2` deprecated в `proliv-dest`.

**ИНЦИДЕНТ 2026-11-10 - NL упал с ~19:36 09.11 по ~15:25 10.11:** сборка
`nginx 1.28.0-1~focal` из pool nginx.org для focal ломает TLS 1.3 - её
:8443 неготировал только TLS 1.2 (alert `protocol_version`). REALITY требует
TLS 1.3-хендшейк dest'а для мимикри (`isHandshakeComplete: false` ->
`target sent incorrect server hello`), поэтому ВСЕ валидные клиенты помечались
невалидными и стылились (клиент видел настоящий LE-серт -> "received real
certificate"). Диагностика: auth в debug-логе проходит нормально, падает
именно стил-хендшейк; `openssl s_client -tls1_3` к `127.0.0.1:8443` -> alert.
**Фикс:** откат на штатный `nginx 1.18.0-0ubuntu1.7` (TLS 1.3 с системным
libssl1.1 работает), `ssl_reject_handshake` заменён паттерном для <1.19.4:
default_server с self-signed `snakeoil.pem` (CN=localhost) + `return 444` -
чужой SNI получает обрыв без утечки домена. Ставить nginx из pool nginx.org
на focal НЕЛЬЗЯ. На KZ 1.28.3 (Ubuntu 22.04, OpenSSL 3.0.2) - TLS 1.3 в
порядке, не трогать.

**Фул-харденинг всех нод (2026-11-09, 6/6):**

- `server_tokens off` + `ssl_protocols TLSv1.2 TLSv1.3` в http{} на всех.
  Server-заголовок теперь голый `nginx` без версии/ОС.
- Ping выключен: `net.ipv4.icmp_echo_ignore_all=1` в `/etc/ufw/sysctl.conf`
  (ufw при reload перетирает `/etc/sysctl.d/*` — править только там) + live
  sysctl + `echo-request -> DROP` в `before.rules`/`before6.rules` (v4+v6).
- sshd: `PasswordAuthentication no`, `PermitRootLogin prohibit-password`,
  `ufw limit 22/tcp`.
- Наружу только 22/80/443 (+ 2222/2223 только с IP панели). `:8444` (legacy
  WS-вход) переведён на `127.0.0.1` в `sites-enabled/proliv-ws` на DE/UK/EE,
  UFW-правило снято. На NL `:8444` = yt-socks (python3), уже ограничен
  UFW списком IP нод — оставлен.
- `telemt` (MTProto) живёт только на FI (`:465`, UFW allow). На EE остановлен
  и снят с автозапуска (`systemctl disable --now`), правила `465/2083/10443`
  удалены.
- FI: ufw вообще не стоял — установлен и настроен с нуля (deny in/allow out,
  22 limit, 80, 443, 465, 2222 с панели).
- Бан сканеров: 40 v4 DENY-правил (Censys 16x/24, Shodan ~10 сетей,
  Shadowserver 5, Expanse 3) через `ufw insert`; v6 — DROP-цепочкой в
  `before6.rules` (ufw не умеет insert для v6).
- Проверка: свой SNI -> 200 на всех, чужой -> TLS-reset, `icmp_echo_ignore_all=1`,
  пинг нода->нода молчит.
- Декои: у каждой ноды локализованный сайт с geo-метой под локацию
  (de/en/et/fi/nl/kk lang + placename/geo.region/ICBM).

**Зависимость: YouTube у всех локаций идёт через NL.** В xray-конфиге всех
нод глобальный routing: домены `geosite:youtube`, `googlevideo`, `ytimg`,
`ggpht`, `youtube-nocookie`, `youtubei.googleapis.com`, `youtube.googleapis.com`
-> outbound `yt-via-nl` -> socks5 `87.58.201.121:8444` (python3 на NL, креды
`iv1dgh3bma`, UFW пускает только IP нод). YT выходит в сеть с IP нидерландов
независимо от выбранной локации. Следствие: падение NL или его :8444 ломает
ютуб ВЕЗДЕ, даже если сам выход локации жив. Проверка с любой ноды:
`curl -x socks5://iv1dgh3bma:***@87.58.201.121:8444 https://www.youtube.com/`.

## DNS (Яндекс DNS-хостинг зоны proliv-network.xyz)

| Имя | Тип | Значение |
|-----|-----|----------|
| `ee.proliv-network.xyz` | CNAME | `1540ec66beea3fbe.topology.gslb.yccdn.ru` (yccdn edge) |
| `ee-src.proliv-network.xyz` | A | `31.76.70.98` (нода, источник CDN + REALITY-ссылка) |

Yandex CDN-ресурс `ee.proliv-network.xyz`: источник `ee-src.proliv-network.xyz`
(группа `common-ee-src-proliv-network-xyz`), протокол HTTPS, "Заголовок Host" =
Своё значение -> `ee.proliv-network.xyz`, серт `main` из Certificate Manager
(Managed, уже был Issued). gslb-домен тот же, что у de - edge различает ресурсы
по Host.

## Панель Remnawave (не трогать Default-Profile!)

`Default-Profile` (`00000000-0000-0000-0000-000000000000`) общий для DE и UK —
любой патч его портов ломает сразу две ноды. Под каждую CDN-ноду — свой профиль.

`EE-Profile` = `9110bb10-a34c-4e75-b3fc-f9e1c5cf4a57`:

| inbound | tag | порт | listen |
|---------|-----|------|--------|
| `2bb325fa-f261-4303-9957-59610359b76f` | `VLESS-TCP-Reality-EE` | 10443 | `0.0.0.0` |
| `1ed61b6d-8b3c-49fc-a865-3fcca3aeb153` | `VLESS-WS-CDN-EE` | 9443 | `127.0.0.1` |
| `2e302a60-6966-4a1c-acc5-de4935db3dfb` | `VLESS-XHTTP-CDN-EE` | 9444 | `127.0.0.1` |

После создания профиля обязательно:

1. `PATCH /nodes/` — привязать ноду к новому `activeConfigProfileUuid` + `activeInbounds`.
2. `PATCH /hosts/` — перевесить хосты на новые `configProfileInboundUuid`.
3. `PATCH /internal-squads` `{uuid, inbounds: [...]}` — **добавить новые inbound-uuid
   в Default-Squad** (`2b5f5dcd-0099-4f51-bc26-0ba04c240d63`), иначе хосты не
   попадут в подписку (уже ловили: ссылки на Эстонию пропали из выдачи).

Хосты (после сплита 2026-11-08):

| remark | address:port | sni | host | inbound | nodes |
|--------|--------------|-----|------|---------|-------|
| `🇪🇪 Эстония` (вкл) | `ee-src.proliv-network.xyz:10443` | `ee.proliv-network.xyz` | — | Reality-EE (EE-Profile) | — |
| `🇪🇺 x2 LTE доступ №1` | `ee.proliv-network.xyz:443` | `ee.proliv-network.xyz` | `ee.proliv-network.xyz` | XHTTP-CDN-EE-LTE `f0e3e463` (EE-LTE-Profile) | EE-Node-LTE |

У CDN-хоста: `mode: packet-up`, `path: /media/feed/preview/`, ALPN `h2,http/1.1`,
fp `chrome`, `nodes: [EE-Node]`.

## xhttp extra — критично

**Единый набор для yccdn (EE + DE, с 2026-11-05):** `uplinkDataPlacement: "header"`
- у Яндекс-эджа любое тело запроса = 413, аплинк едет в заголовке
`X-Playback-Token`. Имена `sess_id`/`X-Playback-Token`/`X-Media-Token`/`_t`
нестандартные - эджи режут дефолтные `x_padding`.

```json
{
  "xmux": {
    "cMaxLifetimeMs": 0,
    "cMaxReuseTimes": "1000",
    "maxConcurrency": "0",
    "maxConnections": "2-4",
    "hMaxRequestTimes": "600-900",
    "hMaxReusableSecs": "100",
    "hKeepAlivePeriod": 20
  },
  "seqKey": "segment",
  "sessionKey": "sess_id",
  "xPaddingKey": "_t",
  "seqPlacement": "query",
  "sessionIDKey": "sess_id",
  "uplinkDataKey": "X-Playback-Token",
  "xPaddingBytes": "100-1000",
  "xPaddingHeader": "X-Media-Token",
  "xPaddingMethod": "tokenish",
  "sessionIDLength": "5-8",
  "uplinkChunkSize": 0,
  "sessionPlacement": "query",
  "uplinkHTTPMethod": "GET",
  "xPaddingObfsMode": true,
  "xPaddingPlacement": "header",
  "scMaxEachPostBytes": 65536,
  "sessionIDPlacement": "query",
  "uplinkDataPlacement": "header",
  "serverMaxHeaderBytes": 262144
}
```

Одинаковый JSON идёт и в `streamSettings.xhttpSettings.extra` инбаунда профиля,
и в `xhttpExtraParams` хоста (клиент и сервер должны совпадать). В инбаунде
`scMaxEachPostBytes`/`serverMaxHeaderBytes` дублируются на верхнем уровне
`xhttpSettings`. Патч через API: `PATCH /api/hosts` и `PATCH /api/config-profiles` —
оба на коллекцию с `uuid` в теле (на `/{uuid}` — 404). Ответ GET
`/api/config-profiles`: `response.configProfiles`, GET `/api/hosts`: `response.hosts`.

**EE переведена на этот набор 2026-11-05** при миграции CDNvideo -> yccdn:
инбаунд `VLESS-XHTTP-CDN-EE` (EE-Profile) + хост `🇪🇺 x2 LTE доступ №1`
(`499f8118-d8a0-49f2-becf-9627c0069fb8`). Бэкапы на proliv-main:
`/root/ee-yccdn-profile-backup.json`, `/root/ee-yccdn-host-backup.json`.
Клиенты подтягивают новый extra при обновлении подписки (Happ рефрешит сам).

## nginx на ноде

На `:443` живут **два** vhost'а (`/etc/nginx/sites-enabled/proliv-cdn`):
`server_name ee-src.proliv-network.xyz` и `server_name ee.proliv-network.xyz` -
edge может слать SNI/Host любого из двух имён, оба должны проксировать роуты.
У каждого свой LE-серт (http-01 через `:80`). Внутри:

```nginx
location ^~ /media/feed/preview {
    client_max_body_size 0;
    proxy_pass http://127.0.0.1:9444;
    proxy_http_version 1.1;
    proxy_request_buffering off;
    proxy_buffering off;
    gzip off;
    tcp_nodelay on;
    proxy_socket_keepalive on;
    proxy_set_header Host $host;
    proxy_set_header Connection "";
    proxy_read_timeout 3600s;
    proxy_send_timeout 3600s;
}
```

**Харденинг под header-аплинк (2026-11-05):** в `nginx.conf` http{} добавлены
`large_client_header_buffers 8 64k;` + `client_header_buffer_size 64k;`,
`listen 443 ssl http2`, `location ^~` для `/media/feed/preview` и `/api/xhttp`,
`gzip off; tcp_nodelay on; proxy_socket_keepalive on;` в proxy-локациях.
Бэкап `/etc/nginx` перед правкой: `/root/nginx_bak_1793862374` на EE-ноде.

Всё остальное — отдача маскировочного сайта. Отдельный лог:
`/var/log/nginx/xhttp_access.log` (запросы видны с edge-IP yccdn).
С 2026-11-08 `proxy_pass` ведёт на `127.0.0.1:9445` (LTE-контейнер), не `:9444`.

## Проверка

```bash
# edge -> origin доходит:
curl -sk -o /dev/null -w '%{http_code}' https://ee.proliv-network.xyz/media/feed/preview/?sess_id=t
# 400 = дошло до xray (нет сессии), 403 = резанул edge, 000/timeout = не дошло

# e2e: тест-клиент на proliv-main
docker logs xcli-test --tail 20
curl -sx socks5h://127.0.0.1:10900 -o /dev/null -w '%{size_download}B' \
  https://speed.cloudflare.com/__down?bytes=3000000
```

Конфиг тест-клиента: `/tmp/xcli_cdn.json` на proliv-main.

## Скорость

Замеренное: ~165 КБ/c на 5 МБ. BBR включён на ноде
(`net.ipv4.tcp_congestion_control=bbr`, `net.core.default_qdisc=fq`).

## Яндекс CDN (gslb) — фича: режет тела запросов 413

`1540ec66beea3fbe.topology.gslb.yccdn.ru` -> `188.72.103.4`. Проверено пробами
через `--resolve` на эдж (EE-орджин, access-лог nginx):

| Запрос через эдж | Ответ | Дошёл до ноды |
|---|---|---|
| GET без тела | 400 | да |
| GET **с телом** (даже 6 байт) | **413** | нет — режет эдж |
| POST **с телом** | **413** | нет — режет эдж |
| GET + кастомные заголовки (`X-Playback-Token`, `X-Media-Token`) | 200 | да |

Вывод: Яндекс-эдж отбивает **любое тело запроса** с 413. Сессия поэтому висла:
poll-запросы доходили (`200 0` в логе), аплинк GET+body — нет.
Заголовки, query, кастомные поля — пропускает свободно.

**Решение:** `uplinkDataPlacement: "header"` — данные аплинка едут в заголовке
`X-Playback-Token`, тела нет вообще. С 2026-11-05 применено и на DE, и на EE
(обе на yccdn).

Ресурс в Яндекс Клауде для `de.proliv-network.xyz`:
группа источников `common-de-src-proliv-network-xyz` -> `de-src.proliv-network.xyz`,
протокол HTTPS, "Заголовок Host" = Своё значение -> `de.proliv-network.xyz`
(edge шлёт на источник Host имени фронта — попадает в правильный vhost),
серт Let's Encrypt из Certificate Manager (DNS-челлендж, `_acme-challenge.de`
CNAME -> `*.cm.yandexcloud.net`). Раскатка серта на эджи — до ~15 минут
после Issued, до этого предъявляет дефолтный `*.yccdn.cloud.yandex.net`.

## DE + Яндекс CDN — отличия от EE-схемы

REALITY **не переезжаем**: у DE REALITY на `:443` с `dest: 127.0.0.1:8443`
(self-steal), значит edge -> `de-src:443` -> xray REALITY -> raw TLS в
`127.0.0.1:8443` -> nginx vhost `de-src` (SNI) -> xhttp `:9445`.
С 2026-11-08 xhttp живёт на отдельной ноде `DE-Node-LTE` (см. раздел
"LTE-ноды" выше): инбаунд `VLESS-XHTTP-CDN-DE-LTE` `7cae8e70` в
`DE-LTE-Profile`, listen `0.0.0.0:9445` внутри bridge-контейнера.
Старый `VLESS-XHTTP-CDN` `0b1a9300` снят с DE-Node-01 (исторически он
"активировался только на DE через activeInbounds").

Файл на ноде: `/etc/nginx/sites-enabled/proliv-src` — vhost
`server_name de-src.proliv-network.xyz` на `127.0.0.1:8443 ssl`
(серт LE webroot'ом, `:80` default_server отдаёт ACME),
`location /media/feed/preview` -> `127.0.0.1:9444`, лог `xhttp_access.log`.

DNS: `de` CNAME -> `*.topology.gslb.yccdn.ru`; `de-src` A -> `13.143.192.49`.
**A и CNAME на одном имени конфликтуют** — старую A-запись `de` удалять,
иначе резолверы отвечают по-разному (Google отдавал старую A, Cloudflare уже CNAME).

Хосты:

| remark | address:port | sni | host | inbound | nodes |
|--------|--------------|-----|------|---------|-------|
| `🇩🇪 Германия` | `de-src.proliv-network.xyz:443` | `de.proliv-network.xyz` | — | Reality (Default-Profile) | — |
| `🇪🇺 x2 LTE доступ №2` | `de.proliv-network.xyz:443` | `de.proliv-network.xyz` | `de.proliv-network.xyz` | XHTTP-CDN-DE-LTE `7cae8e70` (DE-LTE-Profile) | DE-Node-LTE |

Проверка орджина до переключения CDN:
`curl -o /dev/null -w '%{http_code}' https://de-src.proliv-network.xyz/media/feed/preview/?sess_id=t`
-> `400` (дошло через REALITY self-steal до xray), `/` -> `200` (decoy).

**Нюанс, найденный на проде:** эдж шлёт на источник SNI = значению
"Заголовок Host" (`de.proliv-network.xyz`), а не домен источника — поэтому
`location /media/feed/preview` -> `:9444` добавлен в **оба** :8443-vhost'а:
`de-src` (`proliv-src`) и `de` (`proliv-tls`), иначе запросы падали в decoy с 404.

**nginx-харденинг (2026-11-02):** в `nginx.conf` http{} добавлены
`large_client_header_buffers 8 64k;` + `client_header_buffer_size 64k;` — иначе
при `uplinkDataPlacement: header` заголовок `X-Playback-Token` >8k ловил бы
431/400 (совпадает с `serverMaxHeaderBytes 262144` в extra). В :8443-vhost'ах
`listen ... ssl http2`, `location ^~ /media/feed/preview` и `^~ /api/xhttp`,
плюс `gzip off; tcp_nodelay on; proxy_socket_keepalive on;` внутри proxy-локаций.
Бэкап `/etc/nginx` перед правкой: `/root/nginx_bak_1793624740`.

E2E 28.10: 3МБ через `de.proliv-network.xyz` (yccdn edge `188.72.103.4`) ->
выход `13.143.192.49`. ~98 КБ/с — уровень EE до дотюнинга.

## Инцидент 2026-11-06: LTE-хосты "не работают" у юзера на Т2

**Симптом:** у raf на мобилке (Т2) оба LTE-хоста мертвы, Telegram "вечное
обновление". Одновременно у него полный шатдаун моб.интернета (регион в
ограничениях, ~60 регионов/сутки по shutdown.fyi).

**Профилирование показало:** инфраструктура жива на 100% — эдж отвечает 400 из
~80 точек check-host.net (вкл. Москва-ДЦ), оба origin 400, заголовки ~9KB
проходят, ноды connected, e2e-тест xray-клиентом с подпиской raf на main дал
выходы 31.76.70.98 (EE) и 13.143.192.49 (DE) ~1.5 МБ/с. Но **в access.log
нод ноль запросов от его попыток** — пакеты до эджа не долетали вообще.

**Причина:** у Т2 активен режим "белого списка" — фильтрация по IP назначения
(TCP SYN проходит, ClientHello до "небелого" IP дропается, SNI-spoof не
помогает). Пул yccdn `188.72.x` (AS215013 Yandex.Cloud — формально яндексовый,
но у операторов свой список /24) в белый список Т2 **не входит**. Поэтому в
окне шатдауна LTE-хосты мертвы наравне со всем остальным небелым интернетом.
Окно у raf: ~08:35-10:45 UTC; в 10:47 его email:5 появился в XHTTP-CDN
accepts на DE, в 11:01 — на EE.

**Быстрая диагностика "LTE не работает":**

1. `curl -sk -o NUL -w '%{http_code}' https://ee.proliv-network.xyz/media/feed/preview/?sess_id=t`
   — 400 = дошло до xray. То же для `de.`.
2. `grep 'media/feed' /var/log/nginx/access.log | tail` на EE (на DE:
   `xhttp_access.log`, источник 127.0.0.1). Если юзер "прямо сейчас жмёт", а
   в логе тишина — пакеты умирают до эджа = оператор/шатдаун, не сервер.
3. В панели `GET /api/nodes` через `http://127.0.0.1:3443` + JWT из
   `/root/.panel-jwt` (нативный :3000 рубит без proxy-заголовков); в xray-логе
   `email: <userId>` = кто реально внутри туннеля (raf = 5).
4. E2E без клиента: из подписки вытащить JSON-конфиг хоста (Happ-UA на
   sub-URL), поправить inbounds listen 0.0.0.0, `docker run --rm
   -p 127.0.0.1:10900:10808 -v cfg:/etc/xray/config.json teddysun/xray` на
   main, `curl -sx socks5h://127.0.0.1:10900 ifconfig.co` = IP ноды.
5. С телефона юзера (на глушилке): `yandex.ru`, `google.com`,
   `ee.proliv-network.xyz` — отделяет белый список от точечного блока.

**Если белый список и эдж вне его:** единственный фикс — фронт на белом IP.
Кандидат: микро-VM в Yandex Cloud (~400р/мес) с IP из основных диапазонов
(`51.250.x`/`84.201.x`/…) + nginx stream/ssl_preread:443 → ee-src/de-src по
SNI, отдельные host'ы `* T2 *` в подписке. Сначала проверить с телефона в
шатдаун, открываются ли `functions.yandexcloud.net`/`api.cloud.yandex.net`
(облачный диапазон 84.201.x) — если да, VM-релей прокатит; если белый только
AS13238-основной (`storage.yandexcloud.net` = 213.180.x открывается, а
84.201.x нет) — VM не поможет, искать фронт на основном диапазоне.

## Прямой REALITY: sockopt-тюнинг (2026-11-02)

Симптом: на прямом `de-src:443` (VLESS-TCP-Reality) загрузка медиа в Telegram
подвисала и отваливала соединения. Лечение: `sockopt {tcpNoDelay, tcpFastOpen}`
на инбаунде `VLESS-TCP-Reality` (Default-Profile) + `sockoptParams` с тем же
на хосте `🇩🇪 Германия` (идёт в XRAY_JSON клиенту). Ядро на ноде уже было
готово: `tcp_fastopen=1`, `bbr`+`fq`. Эффект подтверждён юзером: мгновенная
загрузка медиа (TFO кладёт данные в SYN = -1 RTT на каждый chunk-коннект TG).
Инбаунд общий — тюнинг распространился и на `🇬🇧`/`🇫🇮`. Бэкап профиля:
`/root/reality-tune-backup.json` на proliv-main; откат = `PATCH /api/config-profiles`
с `{uuid, config}` из файла + `PATCH /api/hosts` `{uuid, sockoptParams: null}`.

**Раскатано на все REALITY-хосты (2026-11-02):** `sockoptParams` на `🇬🇧`/`🇫🇮`/`🇪🇪`,
`sockopt` в `VLESS-TCP-Reality-EE` (EE-Profile). Бэкапы: `/root/hosts-tune-backup.json`,
`/root/ee-profile-backup.json` на proliv-main. Ядро: `tcp_fastopen=1` был везде;
на UK-Node-01 и FI-Node-01 добавлены `bbr`+`fq` персистентно —
`/etc/sysctl.d/99-proliv-net.conf` (было cubic/fq_codel).
