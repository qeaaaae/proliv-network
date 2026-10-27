#!/usr/bin/env bash
# Reads trycloudflare URLs from cloudflared@* journals; if changed,
# rewrites infra/tunnel-urls.env, patches shop/.env URL keys and
# recreates affected containers. Idempotent; safe under systemd timer.
set -uo pipefail

BASE=/opt/proliv
URLS_FILE=$BASE/infra/tunnel-urls.env
SHOP_ENV=$BASE/shop/.env
MARKER=$BASE/infra/.tunnel-urls-applied

url_for() { # $1 = port
  journalctl -u "cloudflared@$1.service" -o cat --since "-10 min" 2>/dev/null \
    | grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' | tail -1
}

EDGE=$(url_for 8090)
APP=$(url_for 8082)
SITE=$(url_for 8080)
[ -n "$EDGE" ] && [ -n "$APP" ] && [ -n "$SITE" ] || exit 0

NEW="EDGE_URL=$EDGE
CABINET_URL=$APP
LANDING_URL=$SITE"

OLD=$(cat "$MARKER" 2>/dev/null || true)
[ "$NEW" = "$OLD" ] && exit 0

printf '%s\n' "$NEW" > "$URLS_FILE"

# Patch shop/.env URL keys in-place (idempotent key= replace).
if [ -f "$SHOP_ENV" ]; then
  sed -i \
    -e "s|^WEBHOOK_BASE_URL=.*|WEBHOOK_BASE_URL=$EDGE|" \
    -e "s|^PUBLIC_APP_URL=.*|PUBLIC_APP_URL=$APP|" \
    -e "s|^SUBSCRIPTION_MINI_APP_URL=.*|SUBSCRIPTION_MINI_APP_URL=$APP|" \
    "$SHOP_ENV"
  cd "$BASE"
  if docker compose -f shop/docker-compose.yml -f infra/minishop.compose.yml \
      -f infra/minishop.prod.compose.yml --env-file shop/.env \
      config --services 2>/dev/null | grep -qx backend; then
    docker compose -f shop/docker-compose.yml -f infra/minishop.compose.yml \
      -f infra/minishop.prod.compose.yml --env-file shop/.env \
      up -d backend bot >/dev/null 2>&1 || true
  fi
fi

printf '%s\n' "$NEW" > "$MARKER"
echo "applied: edge=$EDGE app=$APP site=$SITE"
