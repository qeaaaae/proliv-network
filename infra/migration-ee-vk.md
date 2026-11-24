# План миграции: KZ/UK/FI/EE-old + Яндекс CDN гасим, Финляндию меняем на Эстонию

> **УСТАРЕЛО (21.11.2026).** Этот план описывает БОЛЬШУЮ миграцию
> (гашение KZ/UK/FI/EE-old/yccdn), которая НЕ выполнялась. Вместо неё
> сделана вторая Эстония на qwins (163.245.52.213): `EE2-Node-01` +
> `EE2-Node-LTE`. Старая EE остаётся как `🇪🇪 Эстония Резерв`, FI-LTE -
> как `🇪🇺 LTE - Основной 2`, обе yccdn-резервы и все прочие ноды на
> месте. Актуальная топология: `infra/lte-vk.md`, `infra/hosts-subs.md`.
> Документ оставлен как исторический референс API-рецептов
> (они по-прежнему валидны).

## ПРОЧИТАЙ ПЕРВЫМ ДЕЛОМ - правила для исполнителя

1. **НИКОГДА не лезь в UI панели.** Все операции с панелью - только REST API.
   Полные рецепты с готовыми curl-командами: `infra/remnawave-api.md`.
   Если там нет нужного endpoint - сначала прочитай `infra/ops-runbook.md`,
   потом `infra/node-triage.md`. Только если и там нет - спроси у человека.
2. **Все скрипты с heredoc на сервере заканчиваются CRLF-багом.** Пиши
   скрипт в файл, `scp` на сервер, `sed -i 's/\r$//' file && bash file`.
   Никогда не пайпи PowerShell here-string прямо в `ssh ... "bash -s"` -
   `\r` сломает quoting.
3. **Порядок железный: новое поднято и проверено -> потом старое гасим.**
   Никогда не отключай старую ноду/хост до подтверждения что замена работает.
4. Все UUID и IP ниже - АКТУАЛЬНЫЕ на 17.11.2026, сняты с прода.
   Если API вернёт другие - стоп, разобраться, не guessing'ать.

## Суть миграции одной строкой

Новый VPS Эстония (~270 ₽/мес) заменяет Финляндию ЦЕЛИКОМ: принимает роль
LTE-Основного (ex-FI-Node-LTE, контейнер `remnanode-lte`) И роль VPN-ноды
EE (ex-EE-Node-01). Финляндия как страна уходит полностью - и `fi-src`
(VPN), и FI-LTE. Заодно гасим KZ, UK, обе LTE-резервы на yccdn и оба
Яндекс CDN. Остаются: NL, DE, EE-new + LTE только через VK CDN.

## Справочник UUID/IP (актуально на 17.11.2026)

### Профили (`GET /api/config-profiles`)

| Профиль | UUID | Инбаунды в конфиге |
|---|---|---|
| EE-Profile | `9110bb10-a34c-4e75-b3fc-f9e1c5cf4a57` | VLESS-WS-CDN-EE, VLESS-XHTTP-CDN-EE, VLESS-TCP-Reality-EE-443 |
| FI-LTE-Profile | `268460a0-7d23-4d70-8785-95aadcf20530` | VLESS-XHTTP-CDN-FI-LTE (порт 9445) |
| FI-Profile | `9b29115f-ae59-43dd-92d1-09f9d24c38ba` | умирает с FI |
| Default-Profile | `00000000-0000-0000-0000-000000000000` | shared UK/KZ - НЕ ТРОГАТЬ |

### Ноды (`GET /api/nodes`)

| Нода | UUID | IP | Профиль | Судьба |
|---|---|---|---|---|
| DE-Node-01 | `b4393e6a-...` | 13.143.192.49 | DE-Profile | остаётся |
| NL-Node-01 | `3efb985b-...` | 87.58.201.121 | NL-Profile-v2 | остаётся |
| EE-Node-01 | `c0ad1fb9-...` | 31.76.70.98 | EE-Profile | **гасим, заменяет новая** |
| FI-Node-01 | `3b9e800e-...` | 179.253.82.201 | FI-Profile | **гасим** |
| FI-Node-LTE | `4d681342-...` | 179.253.82.201 | FI-LTE-Profile | **гасим, заменяет новая** |
| EE-Node-LTE | `9ff3cb93-...` | 31.76.70.98 | EE-LTE-Profile | **гасим** |
| DE-Node-LTE | `d2e7022b-...` | 13.143.192.49 | DE-LTE-Profile | **гасим** (резерв мёртв) |
| UK-Node-01 | `cefc979e-...` | 31.76.60.63 | Default | **гасим** |
| KZ-Node-01 | `7e3b6a48-...` | 79.183.193.149 | Default | **гасим** |

(полные UUID - `GET /api/nodes`, в таблице сокращены для читаемости;
в командах ниже используй полные - они есть в выводе API)

### Хосты подписки (`GET /api/hosts`)

| Remark | Адрес | UUID | Судьба |
|---|---|---|---|
| 🇪🇺 LTE - Основной | `fi.proliv-network.xyz` | `52805dbb-47a6-4dc6-8856-3acdc98872ea` | **ОСТАЁТСЯ**, nodes -> новая LTE-нода |
| 🇪🇪 Эстония | `ee-src.proliv-network.xyz` | `ae459449-f6ed-4c52-bb66-7ca92f84b9fa` | DNS -> новый IP, остаётся |
| 🇳🇱 Нидерланды | `nl.proliv-network.xyz` | `76fdea1b-...` | остаётся |
| 🇩🇪 Германия | `de-src.proliv-network.xyz` | `94a4ca12-...` | остаётся |
| 🇬🇧 Великобритания | `uk.proliv-network.xyz` | `f5738299-...` | isDisabled |
| 🇫🇮 Финляндия | `fi-src.proliv-network.xyz` | `a7346d07-...` | isDisabled |
| 🇰🇿 Казахстан | `kz.proliv-network.xyz` | `1d54d17a-...` | isDisabled |
| 🇪🇺 LTE - Резерв 1 | `ee.proliv-network.xyz` | `499f8118-...` | isDisabled |
| 🇪🇺 LTE - Резерв 2 | `de.proliv-network.xyz` | `c492c17a-...` | isDisabled |

### Squad

- Единственный squad: `Default-Squad` = `2b5f5dcd-0099-4f51-bc26-0ba04c240d63`
- Все рабочие инбаунды уже в нём. Новая EE-нода и новая LTE-нода
  автоматически получат юзеров - squad трогать НЕ надо.
- `VLESS-XHTTP-CDN-EE` (`2e302a60-...`) в squad НЕТ - это статус-кво,
  не баг миграции. Не добавлять без отдельной задачи.

### DNS (реальные записи, проверено 17.11 через 8.8.8.8)

| Запись | Сейчас | Станет |
|---|---|---|
| `ee-src.proliv-network.xyz` A | 31.76.70.98 | **новый IP** |
| `fi.proliv-network.xyz` A | 178.176.128.203 (VK edge) | НЕ МЕНЯТЬ - это фронт CDN |
| `fi-src.proliv-network.xyz` A | 179.253.82.201 | удалить после гашения FI |
| `rf-src.proliv-network.xyz` A | 48.102.213.215 (Мск VPS) | не трогаем |
| `ee.proliv-network.xyz`, `de.proliv-network.xyz` | 188.72.112.1 (yccdn) | удалить после гашения CDN |

### Цепочка LTE-Основного (как она устроена - важно!)

```
клиент -> VK CDN edge (fi.proliv-network.xyz = 178.176.128.203)
  -> rf-src.proliv-network.xyz (Мск VPS 48.102.213.215,
     nginx stream ssl_preread :443, роутит по SNI)
  -> НОВЫЙ VPS :443  REALITY (self-steal, dest 127.0.0.1:8443)
  -> nginx :8443 vhost fi.proliv-network.xyz (LE-серт)
  -> xray :9445  (контейнер remnanode-lte, FI-LTE-Profile)
  -> выход с IP нового VPS
```

**Ключевое:** VK CDN смотрит НЕ на FI напрямую, а на `rf-src`!
На Мск-VPS (`proliv-node-rf`) файл
`/etc/nginx/stream-enabled/lte-cdn-relay.conf` роутит SNI:
`fi.proliv-network.xyz -> upstream fi_lte -> server 179.253.82.201:443`.
**Переключение LTE = поменять этот IP на новый VPS.** Всё.

## Фаза 0. Подготовка (до 20.11)

1. Купить VPS Эстония ~270 ₽/мес. Требования к железу: 1-2 CPU, 1-2 GB RAM
   хватит (нода + LTE-контейнер + nginx).
2. Сразу после выдачи проверить IP:
   ```
   ssh root@<NEW_IP> "curl -s ipinfo.io"
   # на proliv-main:
   curl -s "http://ip-api.com/json/<NEW_IP>?fields=country,countryCode,isp,org"
   ```
   Если country=RU/IR или isp палевный - требовать замену IP у хостера.
   serv.host-IP были помечены Google как RU - Gemini умирал. Это критично.
3. SSH: добавить алиас `proliv-node-ee-new` в `~/.ssh/config`
   (HostName = новый IP, ключ `~/.ssh/proliv`).
4. DNS: зайти в DNS-панель provil-network.xyz (Yandex DNS-хостинг),
   у записи `ee-src` снизить TTL до 300.

## Фаза 1. Поднять EE-ноду на новом VPS (новая EE-Node-01)

Полный runbook `infra/new-node.md` - выполнять этапы 0-7, отличия:

1. **Профиль = существующий EE-Profile** `9110bb10-a34c-4e75-b3fc-f9e1c5cf4a57`.
   НЕ создавать новый профиль, НЕ клонировать FI-Profile.
2. `POST /api/nodes` -> получить SECRET_KEY -> remnanode compose.
   Имя ноды в панели при создании: `EE-Node-01-new` (потом можно переименовать).
3. Self-steal: `mask-nodes.sh ee` (декой под Эстонию), nginx :8443,
   `ssl_reject_handshake on`.
4. `PATCH /api/nodes` -> `configProfile.activeConfigProfileUuid = 9110bb10-...`.
5. WARP-стек: EE-Profile outbounds `ai-via-warp` -> `127.0.0.1:40001`
   (проверить в конфиге профиля - если 172.17.0.1, всё равно нужен warp,
   LTE-контейнер тоже будет ходить через него). Ставить по warp-ai.md.
6. **Reality serverNames**: в EE-Profile у `VLESS-TCP-Reality-EE-443`
   serverNames = `[uk, de, ee].proliv-network.xyz` - **НЕТ fi.proliv-network.xyz**.
   Для LTE (фаза 3) нужно ДОБАВИТЬ `fi.proliv-network.xyz` в serverNames -
   это делается в фазе 3 через `PATCH /api/config-profiles` (конфиг целиком,
   рецепт в remnawave-api.md). Не делать раньше - чтобы не сломать old EE.
7. Проверка: `docker logs remnanode` -> `· N users`, подключение с тестового
   клиента, `ifconfig.me` через прокси = новый IP.

## Фаза 2. Переключить DNS EE

1. Поменять A-запись `ee-src.proliv-network.xyz` -> новый IP.
2. `dig +short ee-src.proliv-network.xyz @8.8.8.8` - должен отдавать новый IP
   (TTL 300 - до 5 минут на propagation).
3. Обновить подписку в клиенте, подключиться к 🇪🇪 Эстония - работает.
4. **Только после этого** можно гасить старую EE-ноду (фаза 4).

## Фаза 3. LTE-Основной: Финляндию -> Эстонию

Делать ПОСЛЕ того как EE-нода на новом VPS проверена (фаза 1-2).

### 3.1. На новом VPS - второй контейнер remnanode-lte

По схеме `infra/cdn-xhttp.md` (как на FI сейчас):

```
# контейнер remnanode-lte, xhttp :9445, FI-LTE-Profile
docker run -d --name remnanode-lte --network host --restart unless-stopped \
  -e NODE_PORT=2223 \
  -e "SECRET_KEY=$(cat /root/.remnanode-lte-key)" \
  <remnanode image>   # тот же образ что у remnanode
```

- SECRET_KEY: сгенерировать новый или взять с FI (`/root/.remnanode-lte-key`
  на proliv-node-fi - можно скопировать, тогда в панели нода создаётся с тем же ключом;
  проще сгенерить новый и создать ноду в панели с ним).
- В панели: `POST /api/nodes` -> имя `EE-Node-LTE-new` (или `FI-Node-LTE-new`),
  SECRET_KEY из шага выше -> `PATCH /api/nodes` ->
  `configProfile.activeConfigProfileUuid = 268460a0-...` (FI-LTE-Profile).
- Squad: инбаунд `VLESS-XHTTP-CDN-FI-LTE` (`f35340f4-...`) уже в Default-Squad -
  юзеры приедут сами.

### 3.2. WARP для LTE

FI-LTE-Profile outbounds ходят на `172.17.0.1:40001` (docker-мост хоста) -
значит на новом VPS нужен warp-стек (тот же что для EE-ноды, этап 6).
Один warp-стек обслуживает оба контейнера - как на FI сейчас.

### 3.3. nginx на новом VPS - vhost для fi.proliv-network.xyz

Скопировать с FI (`proliv-node-fi`) на новый VPS:

- `/etc/nginx/sites-enabled/proliv` (vhost :80 для ACME+decoy)
- `/etc/nginx/sites-enabled/proliv-tls` (vhost :8443 ssl -> proxy :9445/:9443)
- LE-серт: **скопировать `/etc/letsencrypt/live/fi.proliv-network.xyz/`
  и `archive/` + `renewal/` с FI** - HTTP-01 renewal не пройдёт пока
  fi.proliv A-запись указывает на VK CDN (не на VPS). Серт жив до
  2027-01-28 - за 2 месяца до expiry решить (перевыпуск через DNS-01
  или временный A-record). Скопировать также `fi-src`/`p.` серты не надо.
- `mask-nodes.sh`/decoy-сайты под fi.proliv - nginx root `/var/www/site`
  скопировать с FI (там FI-декой; подойдёт и EE-вариант, не критично).
- `/etc/nginx/conf.d/xhttp-hdr-log.conf` - формат лога xhttp_hdr (логировать
  LTE-трафик, logrotate настроить как на FI - server-hygiene.md).

### 3.4. Reality serverNames - ДОБАВИТЬ fi.proliv-network.xyz

Без этого шага REALITY на :443 отклонит SNI `fi.proliv-network.xyz`
(сейчас в EE-Profile serverNames только uk/de/ee.proliv-network.xyz).

```
GET /api/config-profiles -> найти EE-Profile (9110bb10-...)
в config.inbounds[] найти tag == 'VLESS-TCP-Reality-EE-443'
в streamSettings.realitySettings.serverNames ДОБАВИТЬ "fi.proliv-network.xyz"
PATCH /api/config-profiles  {"uuid":"9110bb10-...","config":<весь config>}
```

Рецепт PATCH - `remnawave-api.md` -> «Обновить config профиля».
После PATCH: `ssh proliv-node-ee-new "docker restart remnanode"` (форс-синк).
Старая EE-нода тоже получит этот конфиг - безвредно, её гасим в фазе 4.

### 3.5. Переключить rf-src upstream (САМО ПЕРЕКЛЮЧЕНИЕ)

На `proliv-node-rf` (Мск VPS 48.102.213.215):

```bash
ssh proliv-node-rf
cp /etc/nginx/stream-enabled/lte-cdn-relay.conf /etc/nginx/stream-enabled/lte-cdn-relay.conf.bak-20261117
# в файле upstream fi_lte: server 179.253.82.201:443 -> server <NEW_IP>:443
# заодно УДАЛИТЬ мёртвые: строки ee.proliv/de.proliv из map и upstream ee_lte/de_lte
sed -i 's/server 179.253.82.201:443/server <NEW_IP>:443/' /etc/nginx/stream-enabled/lte-cdn-relay.conf
nginx -t && systemctl reload nginx
```

Проверка: `curl -sk -o /dev/null -w '%{http_code}' 'https://fi.proliv-network.xyz/media/feed/preview/?sess_id=t'`
- 400/404 = дошло до xray (хорошо)
- 000/timeout = где-то оборвалось - смотреть цепочку

### 3.6. Панель: host LTE-Основной -> новая нода

`PATCH /api/hosts` для `fi.proliv-network.xyz` (uuid `52805dbb-...`):
поле `nodes` -> UUID новой LTE-ноды (из POST /api/nodes фазы 3.1).
Рецепт PATCH hosts - `hosts-subs.md`.

### 3.7. Проверка e2e LTE

- Обновить подписку, подключиться к `🇪🇺 LTE - Основной`
- `docker logs remnanode-lte` на новом VPS - видны запросы с edge-IP VK
- `/var/log/nginx/xhttp_hdr.log` на новом VPS - hdr-строки от VK edge
- Выход = IP нового VPS

## Фаза 4. Отключить мёртвое в панели (ПОСЛЕ проверок фаз 1-3)

Всё через API (`remnawave-api.md`), НЕ через UI:

### 4.1. Hosts -> isDisabled: true

| Host uuid | Remark |
|---|---|
| `f5738299-a0d1-429d-9cad-3e3d261484bc` | 🇬🇧 Великобритания |
| `a7346d07-5977-4380-aa2f-9905ec5556f1` | 🇫🇮 Финляндия (fi-src!) |
| `1d54d17a-e3b2-4e58-8333-0237fc367da5` | 🇰🇿 Казахстан |
| `499f8118-d8a0-49f2-becf-9627c0069fb8` | 🇪🇺 LTE - Резерв 1 |
| `c492c17a-fd3b-4b44-b173-31f32308606a` | 🇪🇺 LTE - Резерв 2 |

PATCH /api/hosts с `{"uuid":...,"isDisabled":true}` - рецепт в hosts-subs.md.

### 4.2. Nodes -> isDisabled: true

`PATCH /api/nodes` `{"uuid":...,"isDisabled":true}` для:
UK-Node-01, KZ-Node-01, FI-Node-01, FI-Node-LTE, EE-Node-01(old),
EE-Node-LTE, DE-Node-LTE.

### 4.3. DNS cleanup

Удалить A-записи: `fi-src`, `uk`, `kz`, `ee.proliv`, `de.proliv`
(ee-src уже на новом IP - не трогать; fi.proliv - НЕ трогать, это VK фронт!).

## Фаза 5. Гашение VPS/CDN (после 27-29.11)

1. Не продлевать у хостеров: FI, UK, EE-old (Serv.host), KZ (megahost.kz),
   оба Yandex Cloud CDN.
2. Перед отключением Yandex CDN - финальная проверка что на резервах
   нет трафика: `ssh proliv-node-de "docker logs remnanode-lte --since 168h"`
   и то же на EE-old. Если кто-то сидит - предупредить в канале за 3 дня.
3. На DE VPS: `docker rm -f remnanode-lte` (DE-Node-LTE мёртв).
   DE-Node-01 не трогать.
4. `admin_purchases` в minishop DB - удалить/отметить записи FI/UK/KZ/YC-CDN,
   иначе бот будет напоминать об оплате мёртвого:
   ```
   ssh proliv-main "docker exec remnawave-minishop-postgres psql -U remnawave_minishop \
     -d remnawave_minishop -c \"delete from admin_purchases where provider in ('Serv.host','megahost.kz','console.yandex.cloud') and title ~* 'Финляндия|Великобритания|Казахстан|CDN'\""
   ```
   (Сначала SELECT тем же WHERE - проверить что удалится ровно нужное!)

## Фаза 6. Финальный чеклист

- [ ] `GET /api/nodes` - новые EE-Node-01-new + EE-Node-LTE-new isConnected,
      старые disabled
- [ ] `dig ee-src.proliv-network.xyz @8.8.8.8` = новый IP
- [ ] VPN через EE-new: пинг, Gemini, YouTube работают
- [ ] `curl 'https://fi.proliv-network.xyz/media/feed/preview/?sess_id=t'` -> 400/404
- [ ] LTE-Основной в подписке работает, выход = IP нового VPS
- [ ] `docker logs remnanode` на новом VPS: `· N users` на обоих контейнерах
- [ ] NL/DE не пострадали: их хосты isDisabled=false, ноды connected
- [ ] fi.proliv-network.xyz DNS НЕ менялся (A -> VK edge)
- [ ] admin_purchases почищены

## Типовые грабли (FAIL-FAST список)

- **НЕ создавай новую EE-Profile** - только переиспользуй `9110bb10-...`.
- **fi.proliv-network.xyz != fi-src.proliv-network.xyz** - первое живёт
  (VK CDN фронт LTE), второе умирает (VPN Финляндия). В hosts-панели это
  ДВЕ разные записи.
- **Reality serverNames**: без `fi.proliv-network.xyz` в serverNames
  EE-Profile LTE-трафик умрёт на handshake - самая частая ошибка этого
  переезда.
- **rf-src, не VK console**: origin VK CDN = rf-src, переключение через
  nginx stream на Мск-VPS, НЕ через консоль VK (если только ресурс не
  привязан к origin-домену - тогда менять DNS; сейчас A-запись -> VK edge,
  origin настраивается в консоли VK Cloud на rf-src.proliv-network.xyz).
- **LE-серт fi.proliv**: копировать с FI, HTTP-01 не пройдёт через VK CDN.
- **Default-Profile** (UK/KZ) - shared, после гашения останется пустым;
  не трогать и не удалять.
- **Порядок**: новая EE-нода -> DNS ee-src -> LTE-контейнер -> nginx/серт ->
  serverNames -> rf-src upstream -> host nodes -> проверки -> И ТОЛЬКО ПОТОМ
  isDisabled старых. Каждый шаг проверяется до следующего.
- **CRLF**: все удалённые скрипты - через файл + `sed -i 's/\r$//'`.
