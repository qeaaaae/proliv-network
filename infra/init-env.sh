#!/usr/bin/env bash
# Proliv: интерактивная инициализация env на сервере.
# Спрашивает BOT_TOKEN / TG ID / bot username, остальное генерит сам.
# Пишет shop/.env (backend+bot) И proliv.env (frontend).
# Запуск:  bash /opt/proliv/infra/init-env.sh
set -euo pipefail

BASE=/opt/proliv
cd "$BASE"

die() { echo "ERR: $*" >&2; exit 1; }
rand() { openssl rand -hex "${1:-16}"; }

ask() { # $1=prompt $2=varname $3=regex(optional)
  local v
  while :; do
    read -r -p "$1: " v
    v=$(echo "$v" | tr -d "[:space:]")
    if [ -n "${3:-}" ] && [[ ! "$v" =~ $3 ]]; then
      echo "  не похоже на правильное значение, ещё раз"
      continue
    fi
    [ -n "$v" ] && break
    echo "  пусто нельзя"
  done
  printf -v "$2" '%s' "$v"
}

[ -f infra/tunnel-urls.env ] || die "нет infra/tunnel-urls.env - сначала: bash infra/prod-tunnels.sh install"

EDGE=$(grep '^EDGE_URL=' infra/tunnel-urls.env | cut -d= -f2-)
APP=$(grep '^CABINET_URL=' infra/tunnel-urls.env | cut -d= -f2-)
SITE=$(grep '^LANDING_URL=' infra/tunnel-urls.env | cut -d= -f2-)
[ -n "$EDGE" ] && [ -n "$APP" ] && [ -n "$SITE" ] || die "пустые URL в tunnel-urls.env"

echo "=== Proliv init-env ==="

if [ -f shop/.env ]; then
  echo "shop/.env уже существует - использую как есть"
  grep -q '^BOT_TOKEN=..*' shop/.env || die "BOT_TOKEN пуст в shop/.env - впиши токен нового бота"
else
  PANEL_TOK=$(docker exec remnawave-subscription-page printenv REMNAWAVE_API_TOKEN 2>/dev/null || true)
  [ -n "$PANEL_TOK" ] || die "не смог достать REMNAWAVE_API_TOKEN из subpage-контейнера"

  PANEL_WH_SECRET=$(grep '^WEBHOOK_SECRET_HEADER=' proliv.env | cut -d= -f2- | tr -d "[:space:]")
  [ -n "$PANEL_WH_SECRET" ] || die "нет WEBHOOK_SECRET_HEADER в proliv.env"

  echo "Нужно 2 значения, всё остальное сгенерится само."
  echo
  ask "BOT_TOKEN нового бота (из BotFather, вид 123456:AA...)" BOT_TOKEN '^[0-9]+:[A-Za-z0-9_-]+$'
  ask "Твой Telegram user ID (число, @userinfobot)" OWNER_TG_ID '^[0-9]+$'
  echo

  cp infra/minishop.env.prod.example shop/.env
  PARTNER=$(openssl rand -base64 32 | tr '+/' '-_' | tr -d '=')
  sed -i \
    -e "s|__BOT_TOKEN__|$BOT_TOKEN|" \
    -e "s|__OWNER_TG_ID__|$OWNER_TG_ID|" \
    -e "s|__PANEL_API_KEY__|$PANEL_TOK|" \
    -e "s|__PANEL_WEBHOOK_SECRET__|$PANEL_WH_SECRET|" \
    -e "s|__POSTGRES_PASSWORD__|$(rand 16)|" \
    -e "s|__WEBAPP_SESSION_SECRET__|$(rand 32)|" \
    -e "s|__EMAIL_AUTH_SECRET__|$(rand 32)|" \
    -e "s|__PARTNER_KEY__|$PARTNER|" \
    -e "s|__WEBHOOK_URL__|$EDGE|" \
    -e "s|__CABINET_URL__|$APP|g" \
    -e "s|__WEBHOOK_SECRET_TOKEN__|$(rand 32)|" \
    -e "s|__SQUAD_UUIDS__|2b5f5dcd-0099-4f51-bc26-0ba04c240d63|" \
    -e "s|__YK_SHOP_ID__||;s|__YK_SECRET_KEY__||;s|__YK_RETURN_URL__||;s|__YK_RECEIPT_EMAIL__||" \
    shop/.env
  chmod 600 shop/.env
fi

ask "Username бота без @ (например ProlivNetworkBot)" BOT_USERNAME '^[A-Za-z0-9_]+$'

# ---------- proliv.env ----------
# Токен для TG-подписи в кабинете должен совпадать с актуальным BOT_TOKEN
SHOP_TOK=$(grep '^BOT_TOKEN=' shop/.env | cut -d= -f2-)

if ! grep -q 'NUXT_PUBLIC_CABINET_URL' proliv.env; then
  cat >> proliv.env <<EOF

# --- Proliv app deploy ---
NUXT_PUBLIC_LANDING_URL=$SITE
NUXT_PUBLIC_CABINET_URL=$APP
NUXT_PUBLIC_BOT_USERNAME=$BOT_USERNAME
NUXT_PUBLIC_DEV_AUTH=0
EOF
else
  sed -i \
    -e "s|^NUXT_PUBLIC_LANDING_URL=.*|NUXT_PUBLIC_LANDING_URL=$SITE|" \
    -e "s|^NUXT_PUBLIC_CABINET_URL=.*|NUXT_PUBLIC_CABINET_URL=$APP|" \
    -e "s|^NUXT_PUBLIC_BOT_USERNAME=.*|NUXT_PUBLIC_BOT_USERNAME=$BOT_USERNAME|" \
    -e "s|^NUXT_PUBLIC_DEV_AUTH=.*|NUXT_PUBLIC_DEV_AUTH=0|" \
    proliv.env
fi
sed -i "s|^NUXT_BOT_TOKEN=.*|NUXT_BOT_TOKEN=$SHOP_TOK|" proliv.env

# ---------- proliv.env ----------
if ! grep -q 'NUXT_PUBLIC_CABINET_URL' proliv.env; then
  cat >> proliv.env <<EOF

# --- Proliv app deploy ---
NUXT_PUBLIC_LANDING_URL=$SITE
NUXT_PUBLIC_CABINET_URL=$APP
NUXT_PUBLIC_BOT_USERNAME=$BOT_USERNAME
NUXT_PUBLIC_DEV_AUTH=0
EOF
else
  sed -i \
    -e "s|^NUXT_PUBLIC_LANDING_URL=.*|NUXT_PUBLIC_LANDING_URL=$SITE|" \
    -e "s|^NUXT_PUBLIC_CABINET_URL=.*|NUXT_PUBLIC_CABINET_URL=$APP|" \
    -e "s|^NUXT_PUBLIC_BOT_USERNAME=.*|NUXT_PUBLIC_BOT_USERNAME=$BOT_USERNAME|" \
    -e "s|^NUXT_PUBLIC_DEV_AUTH=.*|NUXT_PUBLIC_DEV_AUTH=0|" \
    proliv.env
fi

echo "===== env готово ====="
echo "Поднимаю стек? (y/N)"
read -r -p "> " GO
if [[ "$GO" =~ ^[yYдД]$ ]]; then
  docker compose -f shop/docker-compose.yml -f infra/minishop.compose.yml \
    -f infra/minishop.prod.compose.yml --env-file shop/.env --profile bot up -d
  docker compose --env-file proliv.env --profile dev --profile site --profile app \
    up -d --build devproxy landing cabinet
  echo "===== поднято, проверяй: docker ps ====="
else
  echo "Ок. Подъём вручную:"
  echo "  cd $BASE"
  echo "  docker compose -f shop/docker-compose.yml -f infra/minishop.compose.yml -f infra/minishop.prod.compose.yml --env-file shop/.env --profile bot up -d"
  echo "  docker compose --env-file proliv.env --profile dev --profile site --profile app up -d --build devproxy landing cabinet"
fi
