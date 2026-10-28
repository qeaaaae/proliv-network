# CDN xhttp транспорт (LTE-хосты)

Рабочая схема на примере Эстонии. Цель: прятать VLESS-xhttp за публичный CDN,
чтобы мобильные операторы видели обычный HTTPS к медиа-домену.

## Факт на проде (снято 2026-10-28)

- EE: `ee.` -> CDNvideo (trbcdn), edge -> nginx `:443` на ноде -> xray xhttp `:9444`.
  REALITY-EE живёт на `:10443`, его хост `🇪🇪 Эстония` **выключен** (`isDisabled`) -
  для юзеров EE сейчас LTE-only.
- DE: `de.` -> Yandex CDN (yccdn), edge -> `de-src:443` -> xray REALITY self-steal ->
  nginx `:8443` -> xray xhttp `:9444`.
- На EE-ноде `consumptionMultiplier = 1.7` (CDN-трафик платный) - поэтому в remark
  вручную пишем `1.7x`, юзер видит `🇪🇪 1.7x LTE Эстония`. У DE = 1.
- В подписке хосты выглядят как `VLESS·XHTTP·TLS·JSON` (Happ).

## Топология

```
клиент -> edge CDN (ee.proliv-network.xyz:443)
        -> nginx :443 на ноде (server_name ee.proliv-network.xyz)
        -> xray xhttp 127.0.0.1:9444
        -> выход через IP ноды
```

REALITY на той же ноде вынесен с 443 на `10443`, потому что 443 занимает nginx.

## DNS (Яндекс DNS-хостинг зоны proliv-network.xyz)

| Имя | Тип | Значение |
|-----|-----|----------|
| `ee.proliv-network.xyz` | CNAME | `pibki7stkw.a.trbcdn.net` (CDNvideo edge) |
| `ee-src.proliv-network.xyz` | A | `31.76.70.98` (нода напрямую, для REALITY-ссылки) |

Источник CDN-ресурса: `ee-src.proliv-network.xyz` -> порт 443 (nginx).

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

Хосты:

| remark | address:port | sni | host | inbound |
|--------|--------------|-----|------|---------|
| `🇪🇪 Эстония` (выкл, `isDisabled`) | `ee-src.proliv-network.xyz:10443` | `ee.proliv-network.xyz` | — | Reality-EE |
| `🇪🇪 1.7x LTE Эстония` | `ee.proliv-network.xyz:443` | `ee.proliv-network.xyz` | `ee.proliv-network.xyz` | XHTTP-CDN-EE |

У CDN-хоста: `mode: packet-up`, `path: /media/feed/preview/`, ALPN `h2,http/1.1`,
fp `chrome`, `nodes: [EE-Node]`.

## xhttp extra — критично

Edge CDNvideo **резал 403** любые запросы, где в query или заголовках есть
`x_padding` / `x-padding`. Стандартная extra не работает. Рабочий набор имён:

```json
{
  "xmux": {
    "cMaxLifetimeMs": 0,
    "cMaxReuseTimes": "64-128",
    "maxConcurrency": "48-96",
    "maxConnections": 0,
    "hMaxRequestTimes": "600-1000",
    "hMaxReusableSecs": "1800-3600"
  },
  "seqKey": "segment",
  "sessionKey": "sess_id",
  "xPaddingKey": "_t",
  "seqPlacement": "query",
  "sessionIDKey": "sess_id",
  "uplinkDataKey": "X-Playback-Token",
  "xPaddingBytes": "1-32",
  "xPaddingHeader": "X-Media-Token",
  "xPaddingMethod": "tokenish",
  "sessionIDLength": "5-8",
  "uplinkChunkSize": 0,
  "sessionPlacement": "query",
  "uplinkHTTPMethod": "GET",
  "xPaddingObfsMode": true,
  "xPaddingPlacement": "header",
  "scMaxEachPostBytes": 1000000,
  "sessionIDPlacement": "query",
  "uplinkDataPlacement": "body",
  "serverMaxHeaderBytes": 50000
}
```

Одинаковый JSON идёт и в `streamSettings.xhttpSettings.extra` инбаунда профиля,
и в `xhttpSettings.extra` хоста (клиент и сервер должны совпадать).

## nginx на ноде

На `:443` живут **два** vhost'а (`/etc/nginx/sites-enabled/proliv-cdn`):
`server_name ee-src.proliv-network.xyz` и `server_name ee.proliv-network.xyz` -
edge может слать SNI/Host любого из двух имён, оба должны проксировать роуты.
У каждого свой LE-серт (http-01 через `:80`). Внутри:

```nginx
location /media/feed/preview/ {
    proxy_pass http://127.0.0.1:9444;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_request_buffering off;
    client_max_body_size 0;
    proxy_read_timeout 3600s;
    proxy_send_timeout 3600s;
}
```

Всё остальное — отдача маскировочного сайта. Отдельный лог:
`/var/log/nginx/xhttp_access.log` (запросы видны с edge-IP CDN:
`151.236.x.x`, `185.31.x.x`, эгресс `78.159.252.29`).

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
`X-Playback-Token`, тела нет вообще. На EE не применяем (она на CDNvideo, где
тело разрешено) — используем для DE на Яндексе.

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
`127.0.0.1:8443` -> nginx vhost `de-src` (SNI) -> xhttp `:9444`.
Отдельный профиль не нужен: `VLESS-XHTTP-CDN` (`0b1a9300-...`, listen
`127.0.0.1:9444`) активируется только на DE-ноде через `activeInbounds`,
UK его не поднимает — конфликтов нет. Extra у этого инбаунда = тот же набор,
но `uplinkDataPlacement: "header"`.

Файл на ноде: `/etc/nginx/sites-enabled/proliv-src` — vhost
`server_name de-src.proliv-network.xyz` на `127.0.0.1:8443 ssl`
(серт LE webroot'ом, `:80` default_server отдаёт ACME),
`location /media/feed/preview` -> `127.0.0.1:9444`, лог `xhttp_access.log`.

DNS: `de` CNAME -> `*.topology.gslb.yccdn.ru`; `de-src` A -> `13.143.192.49`.
**A и CNAME на одном имени конфликтуют** — старую A-запись `de` удалять,
иначе резолверы отвечают по-разному (Google отдавал старую A, Cloudflare уже CNAME).

Хосты:

| remark | address:port | sni | host | inbound |
|--------|--------------|-----|------|---------|
| `🇩🇪 ⚡ Германия` | `de-src.proliv-network.xyz:443` | `de.proliv-network.xyz` | — | Reality (Default-Profile) |
| `🇩🇪 LTE Германия` | `de.proliv-network.xyz:443` | `de.proliv-network.xyz` | `de.proliv-network.xyz` | XHTTP-CDN (Default-Profile, активен только на DE) |

Проверка орджина до переключения CDN:
`curl -o /dev/null -w '%{http_code}' https://de-src.proliv-network.xyz/media/feed/preview/?sess_id=t`
-> `400` (дошло через REALITY self-steal до xray), `/` -> `200` (decoy).

**Нюанс, найденный на проде:** эдж шлёт на источник SNI = значению
"Заголовок Host" (`de.proliv-network.xyz`), а не домен источника — поэтому
`location /media/feed/preview` -> `:9444` добавлен в **оба** :8443-vhost'а:
`de-src` (`proliv-src`) и `de` (`proliv-tls`), иначе запросы падали в decoy с 404.

E2E 28.10: 3МБ через `de.proliv-network.xyz` (yccdn edge `188.72.103.4`) ->
выход `13.143.192.49`. ~98 КБ/с — уровень EE до дотюнинга.
