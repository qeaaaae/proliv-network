#!/usr/bin/env bash
# ============================================================================
# ProlivVPN - bootstrap панельного VPS (Ubuntu 24.04 / Debian 12)
#
# Скрипт идемпотентен - повторный запуск безопасен:
#   - Docker не переустанавливается
#   - proliv.env НИКОГДА не перезаписывается
#   - UFW-правила применяются повторно без дублей
#
# Что делает:
#   1. Ставит Docker + compose plugin через get.docker.com (если нет)
#   2. Ставит зависимости: curl, ufw, openssl, git, gettext-base (envsubst)
#   3. UFW: OpenSSH, 80/tcp, 443/tcp, NODE_PORT (tcp+udp, default 443)
#   4. Раскладывает репо в /opt/proliv:
#      - если рядом с ../ есть docker-compose.yml (запуск из репо) - копирует
#      - иначе git clone REPO_URL (для запуска curl | bash)
#   5. Генерит /opt/proliv/proliv.env из proliv.env.example (только если нет)
#   6. Рендерит /opt/proliv/Caddyfile из infra/Caddyfile через envsubst
#   7. Поднимает стек: docker compose --profile site --profile subpage
#      затем Caddy из infra/caddy.compose.yml
#
# Запуск:
#   sudo bash ./infra/deploy-vps.sh                    # из клона репо
#   curl -fsSL <raw-url>/deploy-vps.sh | sudo bash     # потребует REPO_URL
#   sudo DOMAIN=proliv-network.xyz EMAIL=me@mail.com bash ./infra/deploy-vps.sh
#
# Переменные окружения:
#   DOMAIN    - базовый домен (промпт, если не задан)
#   EMAIL     - email для ACME/Let's Encrypt (промпт, если не задан)
#   REPO_URL  - git URL репо (нужен только для curl|bash без локальных файлов)
#   NODE_PORT - порт ноды, открываемый в UFW (default 443)
#   INSTALL_DIR - куда ставить (default /opt/proliv)
#
# Харденинг (вручную после деплоя):
#   - отключить парольный вход SSH:
#       sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' \
#           /etc/ssh/sshd_config && systemctl reload ssh
#     (сначала убедись, что вход по ключу работает!)
#   - fail2ban опционально: apt install fail2ban
# ============================================================================

set -euo pipefail

log()  { printf '\033[1;32m[+]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[!]\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31m[x]\033[0m %s\n' "$*" >&2; exit 1; }

INSTALL_DIR="${INSTALL_DIR:-/opt/proliv}"
REPO_URL="${REPO_URL:-https://github.com/CHANGE_ME/ProlivVPN.git}"  # TODO: прописать реальный URL репо
NODE_PORT="${NODE_PORT:-443}"

# --------------------------------------------------------------------------
[[ "$(id -u)" -eq 0 ]] || die "Run as root, e.g.: sudo bash $0"
command -v apt-get >/dev/null 2>&1 || die "Only apt-based systems are supported (Ubuntu 24.04 / Debian 12)"

# --------------------------------------------------------------------------
# 1. Docker + compose plugin
# --------------------------------------------------------------------------
if command -v docker >/dev/null 2>&1; then
    log "Docker is already installed: $(docker --version)"
else
    log "Installing Docker via get.docker.com ..."
    curl -fsSL https://get.docker.com | sh
fi
docker compose version >/dev/null 2>&1 || die "docker compose plugin is missing - reinstall via get.docker.com or install docker-compose-plugin"
log "Compose: $(docker compose version --short 2>/dev/null || docker compose version)"

# --------------------------------------------------------------------------
# 2. Зависимости
# --------------------------------------------------------------------------
log "Installing dependencies (curl, ufw, openssl, git, gettext-base, ca-certificates) ..."
apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
    curl ufw openssl git gettext-base ca-certificates

# --------------------------------------------------------------------------
# 3. UFW
#    Порядок важен: сначала allow OpenSSH, потом enable - иначе отрежем себя.
#    NODE_PORT (default 443) - на случай, если нода живёт на этом же VPS.
#    На ВЫДЕЛЕННОЙ ноде это правило надо сузить до IP панели:
#      ufw allow from <PANEL_IP> to any port ${NODE_PORT} proto tcp
# --------------------------------------------------------------------------
log "Configuring UFW ..."
ufw allow OpenSSH >/dev/null 2>&1 || ufw allow 22/tcp >/dev/null
ufw allow 80/tcp >/dev/null
ufw allow 443/tcp >/dev/null
ufw allow "${NODE_PORT}/tcp" >/dev/null
ufw allow "${NODE_PORT}/udp" >/dev/null
ufw --force enable >/dev/null
log "UFW status:"
ufw status | sed 's/^/    /'

# --------------------------------------------------------------------------
# 4. Ввод: DOMAIN и EMAIL (env-переменные важнее промпта - для non-interactive)
# --------------------------------------------------------------------------
DOMAIN="${DOMAIN:-}"
if [[ -z "$DOMAIN" ]]; then
    if [[ -t 0 ]]; then
        read -rp "Enter base domain (e.g. proliv-network.xyz): " DOMAIN
    else
        die "DOMAIN env var is required in non-interactive mode (DOMAIN=example.com)"
    fi
fi
[[ -n "$DOMAIN" ]] || die "DOMAIN must not be empty"

EMAIL="${EMAIL:-}"
if [[ -z "$EMAIL" ]]; then
    if [[ -t 0 ]]; then
        read -rp "Enter email for Let's Encrypt (ACME): " EMAIL
    else
        die "EMAIL env var is required in non-interactive mode (EMAIL=you@mail.com)"
    fi
fi
[[ -n "$EMAIL" ]] || die "EMAIL must not be empty"
export DOMAIN EMAIL

# --------------------------------------------------------------------------
# 5. Файлы репо -> INSTALL_DIR
#    - запуск из репо (infra/ рядом с docker-compose.yml): копируем
#    - curl | bash: клонируем REPO_URL
#    - повторный запуск в INSTALL_DIR: ничего не копируем
# --------------------------------------------------------------------------
SCRIPT_DIR=""
if [[ -n "${BASH_SOURCE[0]:-}" && "${BASH_SOURCE[0]}" != "bash" && "${BASH_SOURCE[0]}" != "-bash" ]]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd || true)"
fi

LOCAL_REPO=""
if [[ -n "$SCRIPT_DIR" && -f "${SCRIPT_DIR}/../docker-compose.yml" ]]; then
    LOCAL_REPO="$(cd "${SCRIPT_DIR}/.." && pwd)"
fi

mkdir -p "$INSTALL_DIR"

if [[ -n "$LOCAL_REPO" && "$LOCAL_REPO" == "$INSTALL_DIR" ]]; then
    log "Already inside ${INSTALL_DIR} - skipping copy"
elif [[ -n "$LOCAL_REPO" ]]; then
    log "Copying repo files: ${LOCAL_REPO} -> ${INSTALL_DIR}"
    # .git не тащим; proliv.env и готовый Caddyfile не затираем
    (cd "$LOCAL_REPO" && tar --exclude='./.git' --exclude='./proliv.env' --exclude='./Caddyfile' -cf - .) \
        | tar -xf - -C "$INSTALL_DIR"
elif [[ -d "${INSTALL_DIR}/.git" ]]; then
    log "Existing checkout found in ${INSTALL_DIR} - pulling latest ..."
    git -C "$INSTALL_DIR" pull --ff-only || warn "git pull failed - continuing with current files"
else
    [[ "$REPO_URL" != *CHANGE_ME* ]] || die "REPO_URL env var must point to your git repo (curl|bash mode)"
    log "Cloning ${REPO_URL} -> ${INSTALL_DIR} ..."
    git clone "$REPO_URL" "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"
[[ -f docker-compose.yml ]]      || die "docker-compose.yml not found in ${INSTALL_DIR}"
[[ -f proliv.env.example ]]      || die "proliv.env.example not found in ${INSTALL_DIR}"
[[ -f infra/Caddyfile ]]         || die "infra/Caddyfile template not found in ${INSTALL_DIR}"
[[ -f infra/caddy.compose.yml ]] || die "infra/caddy.compose.yml not found in ${INSTALL_DIR}"

# --------------------------------------------------------------------------
# 6. proliv.env - ТОЛЬКО если отсутствует (никогда не перезаписываем)
#    Секреты по образцу docs.rw/install/remnawave-panel
# --------------------------------------------------------------------------
if [[ -f proliv.env ]]; then
    log "proliv.env already exists - keeping it as is (secrets are NOT rotated)"
else
    log "Generating proliv.env with fresh secrets ..."
    cp proliv.env.example proliv.env

    # 64-байтные hex-секреты (128 hex chars) - как в офиц. рецепте remnawave
    sed -i "s/^APP_SECRET=.*/APP_SECRET=$(openssl rand -hex 64)/" proliv.env
    sed -i "s/^METRICS_PASS=.*/METRICS_PASS=$(openssl rand -hex 64)/" proliv.env
    sed -i "s/^WEBHOOK_SECRET_HEADER=.*/WEBHOOK_SECRET_HEADER=$(openssl rand -hex 64)/" proliv.env

    # Пароль Postgres: 48 hex chars, заодно инжектим в DATABASE_URL
    PG_PASS="$(openssl rand -hex 24)"
    sed -i "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=${PG_PASS}/" proliv.env
    sed -i "s|^\(DATABASE_URL=\"postgresql://postgres:\)[^@]*\(@.*\)|\1${PG_PASS}\2|" proliv.env

    # Домены панели и подписочной страницы
    sed -i "s/^PANEL_DOMAIN=.*/PANEL_DOMAIN=panel.${DOMAIN}/" proliv.env
    sed -i "s/^SUB_PUBLIC_DOMAIN=.*/SUB_PUBLIC_DOMAIN=sub.${DOMAIN}/" proliv.env

    chmod 600 proliv.env
    log "proliv.env generated (chmod 600)"
fi

# --------------------------------------------------------------------------
# 7. Caddyfile из шаблона (envsubst заменяет ${DOMAIN} и ${EMAIL})
# --------------------------------------------------------------------------
log "Rendering Caddyfile for domain ${DOMAIN} ..."
if [[ -f "${INSTALL_DIR}/Caddyfile" ]]; then
    cp -a "${INSTALL_DIR}/Caddyfile" "${INSTALL_DIR}/Caddyfile.bak"
    warn "Existing Caddyfile backed up to Caddyfile.bak"
fi
envsubst '${DOMAIN} ${EMAIL}' < infra/Caddyfile > "${INSTALL_DIR}/Caddyfile"

# --------------------------------------------------------------------------
# 8. Поднимаем стек: pull -> up -d --build -> caddy -> status
#    Caddy стартует последним: ему нужна сеть remnawave-network (external),
#    которую создаёт основной compose, и DNS A-записи для ACME.
# --------------------------------------------------------------------------
log "Pulling images ..."
docker compose --env-file proliv.env --profile site --profile subpage pull --ignore-buildable

log "Starting services (panel + subscription page + landing) ..."
docker compose --env-file proliv.env --profile site --profile subpage up -d --build

log "Starting Caddy reverse proxy ..."
PROLIV_DIR="$INSTALL_DIR" docker compose -f infra/caddy.compose.yml up -d

log "Current status:"
docker compose --env-file proliv.env --profile site --profile subpage ps
PROLIV_DIR="$INSTALL_DIR" docker compose -f infra/caddy.compose.yml ps

# --------------------------------------------------------------------------
# 9. Next steps
# --------------------------------------------------------------------------
cat <<EOF

====================================================================
 Deployment finished.

   Landing : https://${DOMAIN}
   Panel   : https://panel.${DOMAIN}
   Subs    : https://sub.${DOMAIN}

 Next steps:

   1. Open https://panel.${DOMAIN} in a browser - on first visit
      Remnawave prompts you to create the superadmin account.
      TODO (verify command in docs.rw): first admin may also be
      created via CLI:
          docker exec remnawave node dist/scripts/create-admin
      Documented rescue CLI (reset superadmin, get node SECRET_KEY,
      reset certs): docker exec -it remnawave cli

   2. Panel -> Settings -> API Tokens: create a token, paste it into
      SUBPAGE_API_TOKEN in ${INSTALL_DIR}/proliv.env, then restart:
          cd ${INSTALL_DIR}
          docker compose --env-file proliv.env --profile site --profile subpage up -d

   3. If Caddy shows cert errors - check that A-records for ${DOMAIN},
      panel.${DOMAIN} and sub.${DOMAIN} already point to this server:
          PROLIV_DIR=${INSTALL_DIR} docker compose -f infra/caddy.compose.yml logs -f

   4. VPN nodes (EE / UK / ...): deploy them later with
      infra/node.compose.yml on each node VPS - see infra/vps-setup.md.

   5. Hardening (manual):
      - disable SSH password auth (PasswordAuthentication no in
        /etc/ssh/sshd_config, then systemctl reload ssh)
      - optional: apt install fail2ban

====================================================================
EOF
