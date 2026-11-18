# Триаж «не работает»: нода / локация / подписка

Decision tree для агента. Главный принцип: **не паниковать и не «чинить»
наугад — идти по шагам, каждый отвечает на конкретный вопрос.**

## Золотые правила (нарушать = глупые вопросы)

1. **Пинг НЕ является проверкой ноды.** На всех нодах ICMP echo-request
   дропается iptables (ставит `mask-nodes.sh`, анти-скан). `ping` молчит
   = норма. Проверять только TCP.
2. **HTTP 200 на странице ≠ сервис работает.** Gemini отдаёт shell 200
   даже когда внутри «not supported». Проверять реальный ответ/API.
3. **`socks5://` ≠ `socks5h://`** в curl: без `h` домен резолвится
   локально и уходит IP-литерал → доменные правила xray обходятся,
   тест врёт. Для проверки роутинга — только `socks5h://`.
4. **Один клиент ≠ вся нода.** «У юзера не работает» сначала проверить
   со своего клиента/с другой ноды, потом копать ноду.

## Шаг 0. Что именно «не работает»?

| Симптом | Куда идти |
|---|---|
| Конкретная локация мертва, остальные живы | Шаги 1-4 (эта нода) |
| Все локации мертвы у одного юзера | Шаг 6 (клиент/подписка/аккаунт) |
| YouTube/Gemini/AI конкретно | `infra/warp-ai.md` матрица |
| LTE-хосты | `infra/lte-vk.md` диагностика |
| Подписка не обновляется / пустая | Шаги 5-6 |

## Шаг 1. Панель: нода на связи?

```bash
ssh proliv-main
export KEY=$(awk -F= "/^PANEL_API_KEY=/{print \$2}" /opt/proliv/shop/.env | tr -d "\"\r")
curl -s -H "Authorization: Bearer $KEY" http://localhost:3443/api/nodes | python3 -m json.tool | grep -A3 -B1 '"name"'
```

- `isConnected: false` → нода не достучалась до панели. Идти на саму
  ноду (шаг 2). Причины: нода выключена, NODE_PORT 2222 закрыт UFW для
  IP панели, секрет протух, remnanode-контейнер упал.
- `isConnected: true` → панель↔нода канал жив, проблема ниже (шаг 3+).

## Шаг 2. SSH на ноду: контейнер и порты

```bash
ssh proliv-node-<cc>
docker ps | grep remnanode          # контейнер Up?
ss -tlnp | grep -E ':443|:2222'     # xray слушает 443? node-port?
docker logs remnanode --tail 30     # ошибки конфига/panel connect?
systemctl is-active warp-svc warp-v4-shim socks-relay 2>/dev/null  # если профиль с warp/relay
ufw status numbered | head -20      # 443 открыт всем? 2222 только панель?
```

- Контейнер не Up → `docker compose up -d` в `/opt/remnanode`,
  смотреть `docker logs`.
- `docker logs` показывает config pull ошибки → секрет/адрес ноды в
  панели неверны (PATCH /api/nodes, см. remnawave-api.md).
- Порт 2222 недоступен с main → UFW: `ufw allow from <PANEL_IP> to any
  port 2222 proto tcp`.

## Шаг 3. Юзеры на инбаундах (классика!)

```bash
ssh proliv-node-<cc> "docker logs remnanode --since 10m | grep -E 'users|error' | tail -10"
ssh proliv-node-<cc> "docker exec remnanode tail -30 /var/log/xray/current"
```

- `VLESS-... · 0 users` или в xray-логе `invalid request user id` →
  **инбаунды профиля не в Default-Squad**. Лечение:
  `GET /api/config-profiles/inbounds` → uuid инбаундов →
  `PATCH /api/internal-squads` полным списком. См. remnawave-api.md,
  инцидент 17.11.
- `N users` (N>0) → юзеры доезжают, проблема в маршрутизации/сервисе.

## Шаг 4. Маршрутизация конкретного домена

```bash
ssh proliv-node-<cc> "docker exec remnanode grep <domain> /var/log/xray/current | tail -5"
# 'taking detour [yt-via-nl]' / '[ai-via-warp]' / '[DIRECT]' — куда ушло
```

Сверить с матрицей `infra/warp-ai.md`. Подозрительные detour'ы:
- google/gemini → `ai-via-warp` = баг (WARP гео RU) → чинить профиль;
- youtube → не `yt-via-nl` = юзер без youtube-правила (другой профиль?);
- AI → `DIRECT` на serv.host-ноде = Google/AI может резать IP → warp.

## Шаг 5. Self-steal / маскировка жива?

```bash
curl -sk https://<cc>.proliv-network.xyz/ | head -20
# должен отдать ДЕКОЙ-САЙТ (статус/блог на языке страны), НЕ vpn-ответ
curl -sk -o /dev/null -w '%{http_code}' https://<cc>.proliv-network.xyz/
```

- Отдаёт VPN-ошибку/пустоту → REALITY сломан или nginx-декой упал:
  `ssh <node> "systemctl status nginx; nginx -t; ss -tlnp | grep 8443"`.
- Если проверяешь чужой SNI/IP — получишь `ssl_reject_handshake` (RST),
  это by design, не баг.

## Шаг 6. Клиент / подписка / аккаунт

Если нода здорова (шаги 1-5 ок), а у юзера нет:

1. Пусть обновит подписку (`profile-update-interval: 6` часов — ждать
   или дёрнуть refresh в клиенте).
2. Другой клиент/устройство — отделяет клиента от аккаунта.
3. Другой Google-аккаунт/инкогнито — для Gemini-банов на уровне аккаунта
   (Google видит один акк с десятков датацентровых IP → sorry-page на
   ЛЮБОМ выходе; отвисает само за 1-2 дня).
4. Клиентский конфиг: если клиент резолвит DNS сам и шлёт IP-литералы —
   доменные правила обходятся (кейс Влада с роутером). Смотреть
   remote DNS/sniffing в клиенте.
5. Подписка пустая/не отдаёт конфиги → `SUBPAGE_API_TOKEN`,
   `GET /api/sub/<shortUuid>` с UA клиента, панель↔minishop.

## Шаг 7. Что НЕЛЬЗЯ делать при триаже

- НЕ открывать NODE_PORT/8444/40001 наружу «для проверки» — только IP
  панели/нод в UFW.
- НЕ выключать ping-drop / fail2ban / sshd key-only «чтобы проверить».
- НЕ править `destOverride`/`sniffing` наугад — `bittorrent` там валит
  xray (инцидент 15.11, все 9 нод легли на 3 минуты).
- НЕ рестартовать remnanode «на всякий случай» — он сам поллит панель;
  рестарт только если конфиг точно не применяется.
- НЕ считать ноду мёртвой по ICMP — только TCP 443.

## Быстрый чеклист «всё ли ок с нодой» (30 секунд)

```bash
ssh proliv-node-<cc> '
  docker ps | grep -c remnanode        # >=1
docker logs remnanode --since 5m | grep -c "users"   # есть строки с N users
ss -tln | grep -c ":443 "             # >=1
systemctl is-active warp-svc 2>/dev/null || true
ufw status | grep -c "443.*ALLOW"     # >=1
'
```

Все 4-5 пунктов зелёные → нода жива, копать клиента/маршрутизацию.

## История инцидентов, которые этот триаж покрывает

- **17.11 NL**: `invalid request user id` → инбаунды не в squad
  (шаг 3).
- **17.11 NL ping**: «нода не пингуется» → ICMP дропается by design,
  TCP 443 жив (золотое правило 1).
- **17.11 Gemini**: «не работает на любой ноде» → клиент слал
  IP-литералы мимо доменных правил (шаг 6.4).
- **15.11**: `destOverride: bittorrent` → все ноды легли (шаг 7).
- **06.11**: LTE мертвы у Т2 → whitelist оператора, не сервер
  (`lte-vk.md`).
- **12.11 FI**: 431 на xhttp → `serverMaxHeaderBytes` (`lte-vk.md`).

## Связанные доки

- `infra/remnawave-api.md` — все API-операции с панелью
- `infra/warp-ai.md` — матрица YouTube/Gemini/AI по нодам
- `infra/lte-vk.md` — LTE/VK CDN диагностика
- `infra/new-node.md` — создание ноды
- `infra/server-hygiene.md` — логи и чистка
- `infra/torrent-block.md` — торрент-политика
