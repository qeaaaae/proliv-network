# WARP-выход для нейросетей (фактура по серверам, обновлено 2026-11-17 вечер)

## Проблема
Google перекрасил IP нод serv.host (DE/EE/FI) в RU — `Gemini Supported: No`.
ChatGPT при этом работал. UK (qwins) и NL (qwins) остались чистыми.

---

## Что реально стоит на серверах (проверено 2026-11-17)

| Нода | WARP | WARP Exit IP | IPv6 | Роутинг AI |
|------|------|--------------|------|------------|
| **DE** | ✅ локальный | Cloudflare IPv4 (через shim) | нет | `category-ai-chat` → `ai-via-warp` |
| **EE** | ✅ локальный | **104.28.233.140** (CF) | нет | `category-ai-chat` → `ai-via-warp` |
| **FI** | ✅ локальный | **104.28.204.144** (CF) | нет | `category-ai-chat` → `ai-via-warp` |
| **EE2** (qwins, 163.245.52.213) | ✅ локальный (с 21.11) | Cloudflare IPv4 (через shim) | нет | EE2-Profile/EE2-LTE-Profile: AI→`ai-via-warp`, google→`yt-via-nl` |
| **NL** | ✅ локальный | Cloudflare IPv4 (через shim) | **есть** (2a12:bec4:1a80:1c3::2) | NL-Profile-v2: google→`yt-via-nl`, AI→`ai-via-warp` |
| **UK** | ❌ нет | — | нет | DIRECT (пока чистый) |
| **KZ** | ❌ нет | — | нет | DIRECT (пока чистый) |

**WARP на DE/EE/FI с 11.11.2026, на NL тоже, на EE2 с 21.11.2026.** На UK, KZ — нет.

---

## Архитектура WARP на ноде (DE/EE/FI/NL)

```
клиент -> VLESS :443 (Profile) -> xray routing -> outbound ai-via-warp
  -> socks5 127.0.0.1:40001 (warp-v4-shim: домен -> IPv4)
  -> socks5 127.0.0.1:40000 (warp-svc proxy mode) -> Cloudflare edge -> IPv4-эгресс
```

- `cloudflare-warp` (apt из pkg.cloudflare.com) в **proxy-режиме** (`warp-cli mode proxy`, порт 40000) — без TUN, системный маршрут не тронут.
- Регистрация анонимная (consumer), `warp-cli --accept-tos` обязателен в не-TTY вызовах.
- Systemd: `warp-svc` (демон), `warp-v4-shim` (python), `warp-socks-forward` (socat).
- **`/opt/warp-v4-shim.py` (127.0.0.1:40001) — КРИТИЧНАЯ прокладка.** Принимает socks5 CONNECT с доменом, резолвит только в A (IPv4) и шлёт в warp-сокс IPv4-литерал.
  - Без неё warp-демон сам выбирает IPv6-эгресс, а его пул `2a09:bac1::/32` помечен Google как RU/IR.
  - Отключение IPv6 на хосте НЕ помогает — семейство эгресса решает Cloudflare.
- `warp-socks-forward.service`: socat `172.17.0.1:40001 -> 127.0.0.1:40001` — доступ к шиму для bridge-контейнеров (LTE; ufw allow in on docker0).
- Тянет ~170 пакетов зависимостей (cloudflare-warp тащит gtk/webkit-депы; на остальных нодах ставить с `--no-install-recommends`).

---

## yt-via-nl — это НЕ xray, а python socks5-relay

`yt-via-nl` outbound = socks5 на `87.58.201.121:8444` = **`/opt/socks-relay/socks5.py`**
(systemd `socks-relay.service`) на NL-хосте. UFW пускает только IP нод.

**ВАЙТЛИСТ NL `8444/tcp` — ручной.** При смене/добавлении ноды ОБЯЗАТЕЛЬНО
обновить на `proliv-node-nl`:
`ufw allow from <NEW_NODE_IP> to any port 8444 proto tcp comment '<name> yt-socks'`
и удалить старый IP. Инцидент 24.11.2026: EE2 переехал `2.26.182.86` →
`163.245.52.213`, вайтлист не обновили → YouTube+Google (gemini и пр.)
мёртвы на EE2/EE2-LTE, при этом DIRECT и ai-via-warp работали.
Симптом в логах нет — просто timeout на socks-коннекте.
Текущий список: DE 13.143.192.49, UK 31.76.60.63, EE 31.76.70.98,
FI 179.253.82.201, NL 87.58.201.121, KZ 79.183.193.149, EE2 163.245.52.213.

Релей сам выбирает семейство адресов (`open_preferred`):
- YouTube-family (`youtube`, `googlevideo`, `ytimg`, `ggpht`) → **IPv4**
  (NL v4 «сгоревший» от ютуб-нагрузки = degraded mode без рекламы)
- всё остальное → **IPv6 первым** (чистый эгресс, Gemini работает)

Проверено 17.11: `curl -x socks5h://...@87.58.201.121:8444 https://gemini.google.com/`
→ 200, полная страница 935KB. Важно: `socks5://` (не `socks5h://`) в curl
резолвит домен локально и шлёт IPv4-литерал → релей коннектится на этот
литерал → Gemini 403. Реальные xray-клиенты шлют домены — всё ок.

---

## Реальные правила роутинга

**DE/EE/FI (+LTE-профили):**
| Домен | Правило | Outbound |
|-------|---------|----------|
| `geosite:youtube` + youtube-домены | rule 3 | `yt-via-nl` |
| `geosite:google` (включая gemini) | rule 4 | `yt-via-nl` |
| `category-ai-chat-!cn` + reddit | rule 5 | `ai-via-warp` |
| default | — | `DIRECT` |

**NL-Profile-v2 (NL-Node-01, с 17.11):**
| Домен | Правило | Outbound |
|-------|---------|----------|
| `geosite:youtube` + youtube-домены | rule 3 | `yt-via-nl` |
| `geosite:google` + gemini/googleapis | rule 4 (добавлено 17.11) | `yt-via-nl` |
| openrouter/claude/x.ai/perplexity/mistral/openai/anthropic | rule 5 | `ai-via-warp` |
| `codeium.com`, `devin.ai`, `cognition.ai`, `codeium.dev`, `windsurf.com` (добавлено 18.11) | rule 5 | `ai-via-warp` |

До 17.11 в NL-Profile-v2 `gemini.google.com` и `generativelanguage.googleapis.com`
явно шли в `ai-via-warp` → Gemini показывал «не поддерживается в вашей стране».

**Devin/codeium на NL (инцидент 08.11, фикс 18.11):** чат Devin не работал на
NL, хотя `devin.ai` открывался. Причина: бэкенды Devin живут на
`server.codeium.com`/`unleash.codeium.com` (Google Cloud, 34.36.x/35.223.x) —
GCP дропал/резал TCP и отдаёт 403 для IP qwins NL. У codeium нет AAAA-записей
(IPv6 не помогает), NL IPv6 наружу не маршрутизируется. Фикс: домены codeium/
devin/cognition/windsurf добавлены в `ai-via-warp` только в NL-Profile-v2
(остальные ноды codeium пускают direct — их IP чистые для GCP). Симптом:
`unleash.codeium.com` timeout в логе `windsurf_api_client` → «ответа нет» в чате.

---

## Почему Gemini нельзя через WARP

**WARP НЕ пригоден для Google-сервисов** (подтверждено на проде): внутренняя
гео-база Google помечает бесплатный WARP-пул как RU/IR независимо от внешних
geoip. Страница `gemini.google.com` при этом отдаёт HTTP 200 и ~934KB shell —
поэтому curl-тесты «всё ок» врут, реальный ответ «не поддерживается» приходит
на API-вызовах внутри приложения.

- YouTube на том же WARP-эгрессе давал `gl:US`
- Google-поиск — Тегеран (IR)
- Gemini — "не поддерживается в вашей стране"

Поэтому `geosite:google` уходит в `yt-via-nl` → NL IPv6 (на NL-ноде сам релей
выбирает v6 для не-YouTube). WARP оставлен для non-Google AI
(OpenAI/Claude/Grok/Perplexity/Copilot/Mistral) и Reddit.

---

## Полная матрица: куда реально идёт YouTube / Gemini / AI на каждой ноде

Проверено по факту `GET /api/config-profiles` 2026-11-17. Порядок правил
важен: `geosite:youtube`+youtube-домены → `yt-via-nl` (rule 3),
`geosite:google` → `yt-via-nl` (rule 4), AI → `ai-via-warp` (rule 5),
default → DIRECT. Первые три reject-правила (private IP, порты
135-139/445/1900/2869/3702/5353-5358) общие для всех профилей.

| Нода (профиль) | YouTube | Gemini / Google | Прочие AI (claude/openai/…) | Reddit |
|---|---|---|---|---|
| **UK-Node-01, KZ-Node-01** (`Default-Profile`) | `yt-via-nl` → NL IPv4 | **DIRECT с IP ноды** (google-правила нет, IP чистые) | DIRECT | DIRECT |
| **DE-Node-01** (`DE-Profile`) | `yt-via-nl` → NL IPv4 | `yt-via-nl` → **NL IPv6** | `ai-via-warp` → `127.0.0.1:40001` | `ai-via-warp` |
| **EE-Node-01** (`EE-Profile`) | то же | то же | то же | то же |
| **FI-Node-01** (`FI-Profile`) | то же | то же | то же | то же |
| **DE-Node-LTE** (`DE-LTE-Profile`) | то же | то же | `ai-via-warp` → **`172.17.0.1:40001`** | `ai-via-warp` |
| **EE-Node-LTE** (`EE-LTE-Profile`) | то же | то же | `172.17.0.1:40001` | `ai-via-warp` |
| **EE2-Node-01** (`EE2-Profile`) | то же | то же | `127.0.0.1:40001` (WARP IPv4 shim на host-net) | `ai-via-warp` |
| **EE2-Node-LTE** (`EE2-LTE-Profile`) | то же | то же | `172.17.0.1:40001` | `ai-via-warp` |
| **FI-Node-LTE** (`FI-LTE-Profile`) | то же | то же | `172.17.0.1:40001` | `ai-via-warp` |
| **NL-Node-01** (`NL-Profile-v2`) | `yt-via-nl` → релей на самом NL → **NL IPv4** | `yt-via-nl` → **NL IPv6** | `ai-via-warp` → `127.0.0.1:40001` | DIRECT* |

\* В NL-Profile-v2 reddit-доменов в AI-правиле нет — список AI явный
(openrouter, copilot, claude.ai, x.ai, perplexity, mistral, openai,
anthropic), без `category-ai-chat-!cn` и reddit.

**Ключевые факты, которые легко упустить:**

- **LTE-ноды — это второй remnanode-контейнер на ТОМ ЖЕ VPS**, что и
  основная нода страны. WARP у них свой НЕ стоит — `172.17.0.1:40001` это
  docker-мост хоста → `warp-socks-forward` (socat) → шим. Поэтому LTE
  «бесплатно» наследуют WARP DE/EE/FI. Ставить warp на LTE не нужно.
- **UK/KZ — единственные без `ai-via-warp`**: Default-Profile вообще не
  содержит этого outbound'а и AI-правил. Их IP Google до сих пор не
  метил — всё идёт direct.
- **На NL `yt-via-nl` указывает на саму NL** (`87.58.201.121:8444` =
  публичный IP того же хоста). Трафик делает hairpin через свой же
  socks-relay — это нормально и работает, relay слушает на `0.0.0.0:8444`,
  UFW пускает только IP нод (NL сам в списке).
- **Gemini НЕ через WARP нигде** — ни на одной ноде google-домены не
  должны попадать в `ai-via-warp`. Если в логах `gemini.google.com →
  [ai-via-warp]` — это баг роутинга (так было в NL-Profile v1 и в v2 до
  17.11).

---

## История: как Gemini работал (и почему NL был мёртв)

- **До ~10.11.2026**: Gemini на DE/EE/FI шёл DIRECT с IP ноды и работал,
  пока Google не перекрасил IP serv.host в geoip RU.
- **11.11.2026**: Google пометил DE/EE/FI → Gemini умер. В тот же день
  `geosite:google` добавлен в правило `yt-via-nl` (→ NL IPv6), а для
  non-Google AI поднят WARP-стек. С тех пор Gemini на DE/EE/FI+LTE живёт
  через NL IPv6-транзит — схема работает уже больше недели.
- **UK/KZ**: всегда direct, Google их IP не трогал.
- **NL — был мёртв при ЛЮБОМ раскладе**:
  - `NL-Profile` (v1): `gemini.google.com`/`generativelanguage.googleapis.com`
    явно в AI-правиле → `ai-via-warp` → WARP = гео RU/IR → «не
    поддерживается в вашей стране»;
  - `Default-Profile`: google → DIRECT → NL IPv4 `87.58.201.121` = 403
    (IP забанен Google именно для Gemini).
  То есть у NL был чистый IPv6, но google-трафик на него никто не
  направлял.
- **17.11.2026**: в NL-Profile-v2 `geosite:google` + gemini-домены
  переведены с `ai-via-warp` на `yt-via-nl` → Gemini пошёл через NL IPv6.
  Тем же днём: инцидент — NL-профили не были в Default-Squad →
  `invalid request user id` у всех юзеров, вылечено добавлением inbound
  UUIDs в squad (см. `infra/remnawave-api.md`).

Итог сейчас: Gemini работает на ВСЕХ 9 нодах — UK/KZ direct, остальные
через NL IPv6 (на NL — свой IPv6). YouTube везде через NL IPv4.

---

## Профили в панели (Remnawave)

| Профиль | UUID | Outbound AI | Адрес outbound |
|---------|------|-------------|----------------|
| `DE-Profile` | `451b8d6a-218c-4fc3-a1cf-04ca940e6548` | `ai-via-warp` | `127.0.0.1:40001` |
| `EE-Profile` | `9110bb10-a34c-4e75-b3fc-f9e1c5cf4a57` | `ai-via-warp` | `127.0.0.1:40001` |
| `FI-Profile` | `9b29115f-ae59-43dd-92d1-09f9d24c38ba` | `ai-via-warp` | `127.0.0.1:40001` |
| `DE-LTE-Profile` | `11a59109-ce23-46b1-ae7a-bbcbcb2b6b14` | `ai-via-warp` | `172.17.0.1:40001` |
| `EE-LTE-Profile` | `9381c9d1-5c85-4671-8f2f-f0ce7ab6c3ba` | `ai-via-warp` | `172.17.0.1:40001` |
| `FI-LTE-Profile` | `268460a0-7d23-4d70-8785-95aadcf20530` | `ai-via-warp` | `172.17.0.1:40001` |
| `NL-Profile-v2` | `58c03fa0-3724-47ea-a045-47cf139b7f80` | `ai-via-warp` | `127.0.0.1:40001` |
| `NL-Profile` (v1, не используется) | `4a270698-eed5-492e-a6a4-11ed84bbc6a7` | `ai-via-warp` | `127.0.0.1:40001` |
| `Default-Profile` (UK/KZ) | `00000000-0000-0000-0000-000000000000` | **нет** | — |

Управление профилями/нодами — `infra/remnawave-api.md`.

---

## NL IPv4 для Gemini = 403, IPv6 = 200

NL IPv4 `87.58.201.121` забанен Google для Gemini (403 напрямую с хоста).
IPv6 `2a12:bec4:...` чистый (200). Контейнер `remnanode` **без IPv6** —
xray внутри физически не может выйти в v6, поэтому весь google-трафик
идёт через socks-relay → хост → v6. Не пытаться «починить» IPv6 в
контейнере без отдельной задачи — сломает docker-сеть.

---

## Диагностика

```bash
# WARP жив? (на ноде)
warp-cli --accept-tos status          # Connected / healthy
curl -x socks5h://127.0.0.1:40001 https://api.ipify.org   # CF IPv4

# Gemini через shim — страница 200 это НЕ показатель (shell всегда 200)
# Реальная проверка — в браузере или по API-ответу

# Релей yt-via-nl (с любой ноды или с NL)
curl -x socks5h://iv1dgh3bma:<pass>@87.58.201.121:8444 https://gemini.google.com/

# Куда уходит домен в xray — смотреть detour в логе
docker exec remnanode grep gemini /var/log/xray/current | tail
# 'taking detour [yt-via-nl]' = ок, '[ai-via-warp]' для google = баг роутинга
```

---

## Если WARP-эгресс тоже станет "RU"

1. `warp-cli --accept-tos disconnect && warp-cli --accept-tos connect` — эгресс-IP может смениться.
2. Проверка: `curl -x socks5h://127.0.0.1:40001 https://ifconfig.co/` (v4 = шим работает).
3. Запасной вариант: xray `wireguard`-outbound с кредами из `reg.json` warp-cli.
4. Или выход через другую чистую ноду по образцу `yt-via-nl`.

---

## История изменений

- **2026-11-11** — WARP развёрнут на DE/EE/FI (shim + socat + systemd).
- **2026-11-17** — WARP обнаружен и на NL (warp-svc/shim/socat active).
  NL-Profile-v2 создан с AI→warp, но Gemini через warp мёртв → google
  переведён на yt-via-nl (relay→IPv6). Тот же день: инцидент — NL-профили
  не были в Default-Squad → `invalid request user id` у всех юзеров,
  вылечено добавлением inbound UUIDs в squad (см. `infra/remnawave-api.md`).
- **2026-11-18** — фикс Devin на NL: `codeium.com`/`devin.ai`/
  `cognition.ai`/`codeium.dev`/`windsurf.com` добавлены в `ai-via-warp`
  NL-Profile-v2 (GCP резал/403 для IP qwins NL; IPv6 не помогает — у
  codeium нет AAAA). Проверено: через `127.0.0.1:40001` codeium отвечает.
- **Torrent Blocker plugin** `8794c237` привязан ко всем нодам КРОМЕ NL
  (на NL `PluginService batch error` — снят).<|end_message|><|message_model|>read<|content_invoke_tool_json|>{