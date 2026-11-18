# LTE-доступ через VK Cloud CDN (основной LTE-канал)

Краткий runbook: что это, как юзер подключается, как устроена цепочка,
как диагностировать и как поднять ещё один VK-LTE хост.
Глубокая техника (все грабли VK edge, extra-параметры, инциденты) —
`infra/cdn-xhttp.md`, раздел «VK Cloud CDN + LTE №3 на FI».

## Что есть сейчас (факт из панели, 17.11)

| Хост в подписке | address:port | За чем | Нода | Профиль |
|---|---|---|---|---|
| `🇪🇺 LTE - Основной` | `fi.proliv-network.xyz:443` | **VK Cloud CDN** | FI-Node-LTE | FI-LTE-Profile |
| `🇪🇺 LTE - Резерв 1` | `ee.proliv-network.xyz:443` | Яндекс CDN (yccdn) | EE-Node-LTE | EE-LTE-Profile |
| `🇪🇺 LTE - Резерв 2` | `de.proliv-network.xyz:443` | Яндекс CDN (yccdn) | DE-Node-LTE | DE-LTE-Profile |

«LTE - Основной» = VK-вариант. Резервы на yccdn остаются как fallback —
если VK-эдж ляжет, юзер переключается на резерв руками в клиенте.

## Цепочка трафика (VK)

```
клиент (Happ/Incy, VLESS-xhttp)
  -> VK Cloud CDN edge (fi.proliv-network.xyz, AS-диапазоны VK)
  -> rf-src.proliv-network.xyz  (РФ-релей 48.102.213.215,
     nginx stream ssl_preread :443, роутит по SNI)
  -> FI-нода :443  REALITY (self-steal)
  -> nginx 127.0.0.1:8443 (vhost по SNI, LE-серт)
  -> xray :9445  (контейнер remnanode-lte на FI)
  -> выход с IP FI-ноды (179.253.82.201)
```

CDN видит только `rf-src` — про Финляндию не знает. Юзерский uuid доезжает
до FI целиком, учёт трафика/юзеров на FI-Node-LTE в панели корректный.

## Как юзер подключается (ответ на «как подключать»)

Ничего вручную настраивать НЕ нужно — всё приезжает в подписке:

1. Клиент (Happ/Incy/любой с xhttp) → обновить подписку.
2. В списке серверов появится `🇪🇺 LTE - Основной` — выбрать и
   подключиться. Тот же профиль/подписка, что и обычные локации.
3. Проверка что реально через VK: в клиенте/на ноде выход = IP FI-ноды,
   а в `/var/log/nginx/xhttp_hdr.log` на FI видны запросы с edge-IP VK.

Ручной конфиг не требуется: `xhttpExtraParams` хоста и
`xhttpSettings.extra` инбаунда уже содержат VK-вариант параметров
(отличается от yccdn — см. ниже). Клиент получает их из подписки.

## Зачем VK, а не Яндекс (и наоборот)

- **VK CDN** — российский CDN, его edge-IP в «белых списках» мобильных
  операторов при шатдаунах/whitelist-режиме (инцидент 06.11:
  yccdn-пул `188.72.x` у Т2 в whitelist НЕ входил → LTE-хосты были
  мертвы). Поэтому VK-вариант — **основной** для мобильного LTE-доступа.
- **yccdn (Резерв 1/2)** — остаётся fallback: если VK-эдж/ресурс упадёт
  или его IP попадут под фильтры, юзер переключается на Резерв.
  Проверка перед переключением — curl-проба edge (ниже).

## Отличия VK edge от yccdn (критично при правках)

| | yccdn (ee/de) | VK CDN (fi) |
|---|---|---|
| uplink data заголовок | `X-Playback-Token` | **`X-Asset-Token`** — VK edge вырезает `X-Playback-Token-*` и `X-Media-Token` |
| сессия | query `sess_id` | **cookie `media_sid`** |
| паддинг | header `X-Media-Token` | **query `?_t=`** (obfs-заголовки режутся) |
| метод аплинка | GET | GET |
| `serverMaxHeaderBytes` | 262144 | 262144 — обязателен, иначе 431 (инцидент 12.11) |

Полный рабочий `extra` для VK — в `cdn-xhttp.md` раздел «VK Cloud CDN»,
блок «Рабочий extra». **Не копировать yccdn-extra на VK-хост** — не заведётся.

## Диагностика «LTE-Основной не работает»

```bash
# 1. Edge жив? (400 = дошло до xray, 403 = edge режет, 000 = сеть)
curl -sk -o /dev/null -w '%{http_code}' \
  'https://fi.proliv-network.xyz/media/feed/preview/?sess_id=t'

# 2. Запросы доходят до FI-ноды? (смотрим свежие строки)
ssh proliv-node-fi "tail -20 /var/log/nginx/xhttp_hdr.log"
# пусто при живом юзере = пакеты умирают до edge (оператор/шатдаун),
# не сервер. См. инцидент 06.11 в cdn-xhttp.md.

# 3. xhttp на :9445 жив?
ssh proliv-node-fi "docker logs remnanode-lte --tail 20"
# 'invalid padding ()' пачками = клиент шлёт старый extra —
# обновить подписку на клиенте.

# 4. Нода в панели:
# GET /api/nodes -> FI-Node-LTE isConnected, юзеры на инбаунде
# VLESS-XHTTP-CDN-FI-LTE (в логе 'N users').

# 5. Что видит edge -> tcpdump на FI:
ssh proliv-node-fi "tcpdump -i any -A -s0 'tcp port 9445' | head -50"
# показывает заголовки как их видит xray (edge-добавки X-CDN-*,
# X-Forwarded-*, CDN-Loop).
```

## Как поднять ещё один хост на VK CDN (например, второй LTE-выход)

1. **VPS-донора не надо** — используется та же схема: CDN edge ->
   `rf-src` (РФ-релей) -> целевая нода. Нужна только **нода-приёмник**
   (уже есть: FI-Node-LTE) или новая LTE-нода на существующем VPS
   (как EE/DE-LTE — второй контейнер `remnanode-lte` на хосте).
2. **Профиль**: клон `FI-LTE-Profile` (`268460a0-7d23-4d70-8785-95aadcf20530`),
   новые теги инбаундов с суффиксом страны. `PATCH /api/config-profiles`.
3. **Инбаунд**: `VLESS-XHTTP-CDN-<CC>-LTE`, listen `0.0.0.0:9445` (внутри
   bridge-контейнера), `xhttpSettings.extra` = **VK-вариант** (не yccdn!).
4. **Хост в панели**: `PATCH /api/hosts` — remark `🇪🇺 LTE - <...>`,
   address `<cc>.proliv-network.xyz`, sni/host = front-домен,
   `xhttpExtraParams` = тот же VK-extra, `nodes` = [нода].
5. **Squad**: добавить uuid нового инбаунда в Default-Squad
   (`PATCH /api/internal-squads`, полный список!) — иначе `invalid
   request user id`. См. `remnawave-api.md`.
6. **DNS**: `<cc>.proliv-network.xyz` CNAME -> VK edge-домен ресурса
   (Яндекс DNS-хостинг, как у `fi.` — CNAME на gslb VK).
7. **VK CDN-ресурс** в VK Cloud: origin = `rf-src.proliv-network.xyz`,
   протокол HTTPS, Host header = «Пересылать», кэш всё OFF,
   «Игнорировать Set-Cookie» OFF, сжатие/оптимизация OFF, POST
   недоступен — только GET/HEAD/OPTIONS. Сертификат на edge — из VK
   Certificate Manager.
8. **Nginx на ноде-приёмнике**: vhost для `<cc>-src`/front-SNI на
   `127.0.0.1:8443` (или :443 REALITY self-steal → :8443),
   `location /media/feed/preview` -> `127.0.0.1:9445`,
   `listen ssl http2`, `large_client_header_buffers 8 64k` +
   `client_header_buffer_size 64k` в nginx.conf (иначе 431).
9. **Проверка e2e**: curl-проба edge -> 400; реальный клиент из
   подписки -> выход = IP ноды; `xhttp_hdr.log` показывает запросы.

## Связанные доки

- `infra/cdn-xhttp.md` — полная техника CDN-xhttp: extra-параметры,
  инциденты 06.11 (Т2 whitelist) и 12.11 (431), yccdn-схема, RF-релей.
- `infra/new-node.md` — runbook ноды с нуля (этапы 0-7).
- `infra/remnawave-api.md` — PATCH hosts/config-profiles/internal-squads.
- `infra/server-hygiene.md` — где лежат логи и как их читать.
