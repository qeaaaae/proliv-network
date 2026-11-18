# Runbook: новая VPN-нода с нуля (для агента/человека)

Полный пайплайн от покупки VPS до рабочей ноды в проде. Все шаги проверены
на живых нодах (DE/EE/FI/UK/NL/KZ). Имена и значения подставлять свои.
Ниже `<CC>` = двухбуквенный код страны в нижнем регистре (`nl`, `kz`...),
`<DOMAIN>` = `proliv-network.xyz` (reality serverNames + CDN-домены).

Панель API - `infra/remnawave-api.md` (все вызовы curl с proliv-main,
`$KEY` из `shop/.env`, `$BASE=http://localhost:3443/api`).

---

## Этап 0. Покупка VPS и DNS

- KVM-виртуализация, Ubuntu 24.04 / Debian 12, 1+ vCPU, 1-2 GB RAM.
- Хостер важен: IP не должен быть в geoip:ru/ir для Google/OpenAI
  (проверка: `curl ipinfo.io`, `ipregion`). Известно-чистые: qwins.co
  (UK/NL), serv.host (DE/EE/FI - Google пометил RU, поэтому AI через WARP),
  KZ-хостер.
- DNS: A-запись `<cc>.<DOMAIN>` -> IP ноды. Используется как SNI в
  reality serverNames и для CDN-инбаунда.

## Этап 1. Базовая подготовка VPS

```bash
# docker
curl -fsSL https://get.docker.com | sh

# ssh-ключи, fail2ban
apt update && apt install -y fail2ban ufw
systemctl enable --now fail2ban

# ufw (порядок важен - сначала открыть SSH текущего порта!)
ufw allow OpenSSH
ufw allow 443/tcp && ufw allow 443/udp     # юзерский VPN-инбаунд
ufw allow from <PANEL_IP> to any port 2222 proto tcp   # ТОЛЬКО панель -> нода
ufw --force enable
```

- SSH только по ключам (`PasswordAuthentication no` в sshd_config,
  предварительно проверив вход по ключу!).
- Пинг глушим (анти-скан): `iptables -I INPUT -p icmp --icmp-type echo-request -j DROP`
  (делает `mask-nodes.sh` в конце, но можно сразу).

## Этап 2. remnanode на VPS

1. Панель: `POST $BASE/nodes` (или UI Nodes -> Management -> "+") -
   address=IP, port=2222 (Node Port). Ответ содержит `uuid` и `secretKey`.
   Если UI удобнее - кнопка "Copy docker-compose.yml" даёт готовый файл.
2. На ноде:

```bash
mkdir -p /opt/remnanode && cd /opt/remnanode
# положить infra/node.compose.yml как docker-compose.yml,
# вписать NODE_PORT=2222 и SECRET_KEY=<secretKey из панели>
docker compose up -d && docker compose logs -f -t
```

3. Проверка: `docker logs remnanode --tail 20` - нода подключилась,
   в панели `isConnected: true`.

## Этап 3. Self-steal (ОБЯЗАТЕЛЬНО, анти-деанон)

Публичный :443 = xray REALITY, который при активном пробинге отдаёт
не VPN, а невинный сайт. Без этого IP палится сканерами.

1. **Nginx-декой на ноде**: локальный nginx слушает `127.0.0.1:8443`
   с LE-сертом домена (или self-signed - reality dest локальный, сертификат
   наружу не уходит). На `default_server` ОБЯЗАТЕЛЬНО
   `ssl_reject_handshake on` - серт отдаём только по своему SNI.
2. **Тематическая заглушка**: `bash infra/mask-nodes.sh <CC>` - пишет
   фейковый статус-пейдж/блог на языке страны (fi=NordMetrics, uk=BritByte
   Journal, de=KursTicker, ee=?, nl=?, kz=Bozjyra), reload nginx, вешает
   iptables DROP на ping, ставит fail2ban. Файл лежит на ноде в
   `/var/www/site/index.html`, бэкап -> `.bak`.
   В репо `infra/mask-nodes.sh` - шаблоны всех стран.
3. **Reality dest** в инбаунде профиля: `127.0.0.1:8443` - невалидный
   VLESS-клиент проваливается в nginx-декой (выглядит как обычный сайт).

## Этап 4. Config profile в панели

1. `GET $BASE/config-profiles` - взять за образец профиль своей "зоны"
   (DE/EE/FI -> ai+warp профиль, UK/KZ -> Default-Profile).
2. Создать НОВЫЙ профиль (`POST $BASE/config-profiles`) или править
   существующий: **теги инбаундов должны быть уникальными на ноду**
   (суффикс `-<CC>`: `VLESS-TCP-Reality-<CC>` и т.д.) - иначе ноды
   перепутают inbound'ы.
3. Инбаунды (3 шт, как у всех):
   - `VLESS-TCP-Reality-<CC>` :443 tcp, reality, dest `127.0.0.1:8443`,
     serverNames = все `<cc>.<DOMAIN>` + чужие (список общий).
   - `VLESS-WS-CDN-<CC>` :9443 127.0.0.1 ws (за CDN).
   - `VLESS-XHTTP-CDN-<CC>` :9444 127.0.0.1 splithttp/xhttp (за CDN).
   - `sniffing.destOverride`: ТОЛЬКО `["http","tls","quic"]` - другие
     значения (типа `bittorrent`) валят xray при старте (инцидент 15.11).
4. Outbounds: `DIRECT`(freedom), `BLOCK`/`reject`(blackhole),
   `yt-via-nl`(socks 87.58.201.121:8444 - только если это не NL),
   `ai-via-warp`(socks 127.0.0.1:40001 - только если WARP стоит, этап 6).
5. Routing: reject-правила lan-freeze ОБЯЗАТЕЛЬНЫ (private ip, порты
   135-139/445/1900/2869/3702/5353-5358 -> reject) + youtube/google ->
   yt-via-nl + ai-chat -> ai-via-warp. Точные правила - копировать из
   существующего профиля зоны, не выдумывать.
6. `PATCH $BASE/config-profiles` с полным `config`.

## Этап 5. Привязка и squad (КРИТИЧНО)

1. `PATCH $BASE/nodes` -> `{"uuid":"<node>","configProfile":
   {"activeConfigProfileUuid":"<profile>","activeInbounds":[]}}`
2. **Squad**: `GET $BASE/config-profiles/inbounds` -> взять uuid трёх
   новых инбаундов -> `GET $BASE/internal-squads` -> `PATCH
   /api/internal-squads` с ПОЛНЫМ списком (старые + новые).
   Пропуск = `invalid request user id` у всех юзеров (инцидент 17.11).
3. Проверка: `ssh <node> docker logs remnanode --since 5m | grep users` -
   должны быть строки `VLESS-...-<CC> · N users`.

## Этап 6. Опционально: WARP для AI (если профиль с ai-via-warp)

Копия схемы DE/EE/FI/NL - `infra/warp-ai.md`:
- `cloudflare-warp` proxy-режим (порт 40000), `warp-v4-shim.py`
  (127.0.0.1:40001), `warp-socks-forward` socat для docker0 (172.17.0.1:40001).
- БЕЗ шима warp уходит в IPv6-эгресс `2a09:bac1::/32` = Google видит RU.
- Systemd-юниты: `warp-svc`, `warp-v4-shim`, `warp-socks-forward`.
- Gemini через WARP НЕ работает (гео RU/IR) - google-домены всегда
  в `yt-via-nl`, warp только для non-Google AI.

## Этап 7. Torrent Blocker + финальная проверка

1. `PATCH $BASE/nodes` -> `activePluginUuid` = `8794c237-8543-4261-992f-
   fa3b5af495b8` (torrent blocker, blockDuration 3600). На NL не работает
   (`PluginService batch error`) - туда не вешать.
2. Финал:
   - панель: `isConnected: true` у ноды;
   - `ssh <node> docker exec remnanode tail -20 /var/log/xray/current` -
     принимает коннекты;
   - клиент: обновить подписку, подключиться, `curl ifconfig.me` через
     VPN = IP ноды;
   - `mask8443` страница отдаётся по SNI домена ноды (self-steal жив).

## Чеклист одной строкой

VPS+DNS -> docker+ufw -> remnanode+SECRET_KEY -> nginx-decoy+mask-nodes.sh
-> config-profile (уникальные теги!) -> node->profile PATCH -> squad PATCH
-> [warp если AI] -> torrent-plugin -> verify users+connect.

## Типовые грабли

- Забыть squad -> все юзеры `invalid request user id` (см. этап 5).
- Одинаковые теги инбаундов у двух профилей -> ноды путают inbound'ы.
- `destOverride` со значением `bittorrent` -> xray не стартует.
- NODE_PORT открыт на 0.0.0.0/0 -> палит ноду сканерам, только IP панели.
- IPv6 в docker-контейнере remnanode нет - не ждать v6-эгресса из xray.
- `socks5://` vs `socks5h://` в curl-тестах relay'я: без `h` домен
  резолвится локально и тест врёт.
