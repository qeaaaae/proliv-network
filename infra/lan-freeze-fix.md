# Фикс фризов VPN при открытии Проводника / аплоаде файлов (Windows)

Применено на проде 2026-11-13. Симптом: при открытии Проводника или
диалога выбора файла (аттач в Telegram/Discord) весь VPN-коннект подвисал
на ~5 секунд.

## Причина

Проводник и common file dialog при открытии делают сетевую разведку:
пробы мёртвых сетевых шар (SMB :445, NetBIOS :137-139), broadcast/мультикаст
name resolution (NBNS 255.255.255.255:137, mDNS 224.0.0.251:5353,
LLMNR 224.0.0.252:5355, SSDP 239.255.255.250:1900, WSD :3702).
В TUN-режиме эти пакеты летели в туннель: L3-интерфейс broadcast не умеет,
пакеты тонули, Windows ждала таймауты name resolution (~1.5с x повторы = 4-6с),
попутно очередь TUN зашпамливалась - видимый фриз всего соединения.

Усиливало: dead mapped drives / UNC-пути из истории, WebDAV-редиректор
(WebClient), Discord STUN-флуд (sing-box issue #1925), аплоад по TCP-транспорту.

## Что сделано (оба слоя, defence in depth)

### 1. Клиент - шаблон подписки XRAY_JSON (Happ и все JSON-клиенты)

Happ прогоняет JSON-конфиг подписки 1:1 (свои routing-rules приложения на него
не действуют), поэтому правки сделаны прямо в шаблоне, а не заголовком `routing`.

`PATCH /api/subscription-templates` -> шаблон `Default` (XRAY_JSON,
uuid `3a575487-4b1d-47da-901e-9e928254385a`), `templateJson.routing.rules`:

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

- `geoip:private` был, добавлены мультикаст `224.0.0.0/4`, бродкаст
  `255.255.255.255/32`, IPv6-mcast `ff00::/8` -> уходят direct в физический
  адаптер, как без VPN.
- Порядок важен: правило `ip` (private/mcast -> direct) стоит ДО портовых
  блоков - LAN-шары (`\\192.168.x.x`) продолжают работать.
- Порты 135-139/445 и UDP-дискавери к public IP -> block (мгновенный отказ
  ядра клиента, без таймаута).
- Применится у клиентов после обновления подписки (`profile-update-interval: 6`
  часов) + переподключение.

### 2. Ноды - config profiles (все 7 штук)

`PATCH /api/config-profiles` -> в `config` каждого профиля:

- добавлен outbound `{"tag":"reject","protocol":"blackhole","settings":{"response":{"type":"http"}}}`
  (TCP получает 403+close мгновенно вместо silent-drop таймаута);
- в `routing.rules` ПЕРЕД всеми остальными правилами:

```json
[
  {"type":"field","ip":["geoip:private","224.0.0.0/4","255.255.255.255/32","ff00::/8"],"outboundTag":"reject"},
  {"type":"field","network":"tcp,udp","port":"135-139,445","outboundTag":"reject"},
  {"type":"field","network":"tcp,udp","port":"1900,2869,3702,5353,5355,5357-5358","outboundTag":"reject"}
]
```

Закрывает пробы от клиентов без свежего шаблона (mihomo/sing-box/base64)
и попутно дыру: доступ во внутреннюю сеть ноды и cloud metadata
`169.254.169.254` через VPN теперь режется.

## Проверка

- `GET /api/sub/<shortUuid>` с UA Happ: 9 конфигов, routing содержит новые
  правила в каждом.
- Все 9 нод `isConnected: true` после пуша конфига (xray перевалидировал).
- Бэкап до-состояния: `/root/proliv-routing-backup.json` на proliv-main.

## Откат

- Шаблон: `PATCH /api/subscription-templates` uuid `3a575487-...`,
  `templateJson.routing.rules` вернуть к 4 правилам из бэкапа.
- Профили: `PATCH /api/config-profiles` - убрать `reject` outbound и
  3 первых правила (полный слепок в бэкапе).

Апдейт 2026-11-13 (второй заход): в discovery-список добавлены `2869`
(UPnP) и `5357-5358` (WSD/WS-Eventing по HTTP - сетевое обнаружение Windows).
После правок: обычный Проводник не висит; остаточный фриз именно файлового
диалога (скрепка в TG/Discord) - проверять на клиенте: `net use` (мёртвые
маппинги), Credential Manager, служба WebClient (WebDAV) -> Disabled,
OneDrive Files On-Demand.

## Что сервером НЕ закрыто (клиентские факторы)

- Выбор TUN provider/mode в Happ, MTU туннеля (дефолт sing-box 9000),
  mux/TCP-in-TCP насыщение при аплоаде.
- Windows-гигиена юзера: dead `net use` маппинги, WebClient, LLMNR/NetBIOS.
- Если баг останется: диагностика - `ping -t` во время фриза (пинг умирает =
  очередь TUN), CPU `svchost DNS Client` (STUN-флуд Discord), лог клиента
  на флуд 137/138/445/5353/5355.
