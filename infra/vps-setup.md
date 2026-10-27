# ProlivVPN - развёртывание панельного VPS (runbook)

Пошаговая инструкция: от покупки VPS до рабочей панели + subscription page + лендинга.
Архитектура и тарифы - см. `SPEC.md` в корне репо.

## 0. Что получится после деплоя

| URL | Что | Сервис |
|---|---|---|
| `https://<domain>` | Лендинг (Nuxt static + nginx) | `landing` (profile `site`) |
| `https://panel.<domain>` | Remnawave panel | `remnawave:3000` |
| `https://sub.<domain>` | Subscription page | `remnawave-subscription-page:3010` |

Реверс-прокси - Caddy (отдельный compose `infra/caddy.compose.yml`), сертификаты
Let's Encrypt выписывает автоматически. Все backend-порты слушают только
`127.0.0.1` / docker-сеть - наружу торчат лишь 80/443 (Caddy) и SSH.

## 1. Купить VPS

- KVM-виртуализация (не OpenVZ/LXC), 1+ vCPU, 1-2 GB RAM, 20+ GB SSD.
- ОС: **Ubuntu 24.04 LTS** или **Debian 12** (под них написан `deploy-vps.sh`).
- root-доступ по SSH (лучше сразу по ключу).

## 2. DNS

В панели DNS-провайдера создать A-записи на IP сервера:

| Запись | Куда |
|---|---|
| `@` (= `<domain>`) | IP VPS |
| `panel` | IP VPS |
| `sub` | IP VPS |

Позже (не сейчас): `wp.` (TG-прокси), `app.` (mini app), `cdn-ee.`/`cdn-uk.` (origin нод).

Проверка с локальной машины: `dig +short panel.<domain>` должен вернуть IP VPS.
**ACME не выдаст сертификат, пока DNS не смотрит на сервер.**

## 3. Доставить репо на сервер

Вариант A - git clone:

```bash
git clone <repo-url> /root/ProlivVPN && cd /root/ProlivVPN
```

Вариант B - rsync/scp с локальной машины:

```bash
rsync -avz --exclude .git ./ root@<IP>:/root/ProlivVPN/
ssh root@<IP> "cd /root/ProlivVPN"
```

## 4. Запустить bootstrap

```bash
cd /root/ProlivVPN
bash ./infra/deploy-vps.sh          # спросит DOMAIN и EMAIL
# или неинтерактивно:
DOMAIN=proliv.net EMAIL=me@mail.com bash ./infra/deploy-vps.sh
```

Скрипт **идемпотентен**: поставит Docker, настроит UFW, разложит файлы в
`/opt/proliv`, сгенерит `proliv.env` с рандомными секретами (только если его нет),
отрендерит `Caddyfile`, поднимет стек и caddy.

Если `bash` ругается `\r: command not found` - файл с CRLF-окончаниями:
`sed -i 's/\r$//' infra/deploy-vps.sh` и запустить снова.

## 5. Первый вход в панель

1. Открыть `https://panel.<domain>` - при первом визите Remnawave предложит
   создать superadmin-аккаунт.
2. TODO (verify command in docs.rw): первый админ также может создаваться
   через `docker exec remnawave node dist/scripts/create-admin`.
3. Rescue CLI (сброс superadmin, получение SECRET_KEY ноды, сброс сертов):
   `docker exec -it remnawave cli`.

## 6. API-токен для subscription page

Страница подписок ходит в API панели по токену (`SUBPAGE_API_TOKEN` в
`proliv.env`). Пока там `change_me` - страница не заработает.

1. Panel -> **Settings -> API Tokens** -> создать токен.
2. `nano /opt/proliv/proliv.env` -> вписать токен в `SUBPAGE_API_TOKEN`.
3. Перезапустить:

```bash
cd /opt/proliv
docker compose --env-file proliv.env --profile site --profile subpage up -d
```

Проверка: `https://sub.<domain>` открывается, ссылка-подписка тестового юзера
отдаёт конфиги.

## 7. Подключить VPN-ноды (EE / UK / ...)

На отдельных VPS (см. SPEC.md п.4.1). Файл-заготовка: `infra/node.compose.yml`.

1. В панели: **Nodes -> Management -> "+"** -> заполнить форму (address = IP
   ноды, Node Port = 2222) -> кнопка **"Copy docker-compose.yml"** даст готовый
   конфиг с `SECRET_KEY`. Либо `docker exec -it remnawave cli` -> "Get SECRET_KEY".
2. На VPS ноды:

```bash
curl -fsSL https://get.docker.com | sh
mkdir -p /opt/remnanode && cd /opt/remnanode
# скопировать infra/node.compose.yml как docker-compose.yml, вписать
# NODE_PORT и SECRET_KEY из п.1
docker compose up -d && docker compose logs -f -t
```

3. UFW на ноде: инбаунды открыть всем (443/tcp+udp для VLESS+Reality), а
   `NODE_PORT` - **только для IP панели**:

```bash
ufw allow OpenSSH
ufw allow 443/tcp && ufw allow 443/udp
ufw allow from <PANEL_IP> to any port 2222 proto tcp
ufw --force enable
```

4. В панели: в карточке ноды Next -> выбрать Config Profile -> Create.
   Статус ноды должен стать online.

## 8. Полезные команды

```bash
cd /opt/proliv
docker compose --env-file proliv.env --profile site --profile subpage ps
docker compose --env-file proliv.env --profile site --profile subpage logs -f remnawave
PROLIV_DIR=/opt/proliv docker compose -f infra/caddy.compose.yml logs -f
docker exec -it remnawave cli          # rescue CLI панели
docker exec remnanode xlogs            # логи xray на ноде
```

## 9. Харденинг (вручную)

- [ ] SSH только по ключам: `PasswordAuthentication no` в
      `/etc/ssh/sshd_config`, `systemctl reload ssh` (сначала проверь вход по ключу!)
- [ ] `apt install fail2ban` (опционально)
- [ ] Нестандартный SSH-порт (не забудь его же разрешить в UFW до смены)
- [ ] Бэкап `remnawave-db` (pg_dump по cron + off-site копия) - там юзеры/подписки

## 10. Troubleshooting

| Симптом | Что проверить |
|---|---|
| 502 от Caddy | `docker compose ... logs remnawave`, жив ли upstream; DNS-резолв имён в сети remnawave-network |
| Нет сертификата | DNS A-записи на IP сервера; `PROLIV_DIR=/opt/proliv docker compose -f infra/caddy.compose.yml logs -f` |
| sub.<domain> не работает | `SUBPAGE_API_TOKEN` заполнен? рестарт после правки `proliv.env`? |
| Нода offline | SECRET_KEY/NODE_PORT верны? NODE_PORT доступен с IP панели (UFW)? `docker compose logs -f remnanode` |
