#!/bin/bash
# backup-tg.sh — ежедневный бэкап в Telegram админу одним файлом (00:00)
#
# Шлёт ОДИН архив backup-<date>.tar.gz:
#   panel.dump   — БД remnawave (VPN-юзеры, подписки, ноды, хосты)
#   shop.dump    — БД minishop (аккаунты магазина, платежи, тарифы)
#   configs/     — proliv.env + shop/.env + compose (СЕКРЕТЫ!)
#
# Креды: /opt/proliv/shop/.env (BOT_TOKEN, BOOTSTRAP_OWNER_TELEGRAM_ID).
# Cron: 0 0 * * * /opt/proliv/infra/backup-tg.sh
set -euo pipefail

BASE=/opt/proliv
ENV_FILE=$BASE/shop/.env
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

TOKEN=$(awk -F= '/^BOT_TOKEN=/{print $2}' "$ENV_FILE" | tr -d "\"\r")
CHAT=$(awk -F= '/^BOOTSTRAP_OWNER_TELEGRAM_ID=/{print $2}' "$ENV_FILE" | tr -d "\"\r")
[ -n "$TOKEN" ] && [ -n "$CHAT" ] || { echo "no token/chat"; exit 1; }

DATE_ISO=$(date +%F)
DATE_HUMAN=$(date +%d.%m.%Y)
PKG=$WORK/backup-$DATE_ISO.tar.gz

# --- дампы БД ---
docker exec remnawave-db pg_dump -U postgres -d postgres --format=custom \
  -f /tmp/panel-tg.dump
docker cp remnawave-db:/tmp/panel-tg.dump "$WORK/panel.dump"
docker exec remnawave-db rm -f /tmp/panel-tg.dump

docker exec remnawave-minishop-postgres pg_dump -U remnawave_minishop \
  -d remnawave_minishop --format=custom -f /tmp/shop-tg.dump
docker cp remnawave-minishop-postgres:/tmp/shop-tg.dump "$WORK/shop.dump"
docker exec remnawave-minishop-postgres rm -f /tmp/shop-tg.dump

# --- конфиги/секреты ---
mkdir -p "$WORK/configs"
cp "$BASE/proliv.env" "$BASE/shop/.env" "$BASE/docker-compose.yml" "$WORK/configs/" 2>/dev/null || true
for f in caddy.compose.yml minishop.compose.yml minishop.prod.compose.yml; do
  [ -f "$BASE/infra/$f" ] && cp "$BASE/infra/$f" "$WORK/configs/"
done
cp /opt/proliv/infra/backup-tg.sh "$WORK/configs/" 2>/dev/null || true

# --- собираем один архив ---
tar czf "$PKG" -C "$WORK" panel.dump shop.dump configs

curl -sf -F "chat_id=$CHAT" -F "document=@$PKG" \
  -F "caption=#backup $DATE_HUMAN ($(du -h "$PKG" | cut -f1))" \
  "https://api.telegram.org/bot$TOKEN/sendDocument" >/dev/null

echo "backup-tg done $DATE_ISO"
