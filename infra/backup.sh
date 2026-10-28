#!/usr/bin/env bash
# Ночной бэкап Proliv: только обе БД (pg_dump custom) + env-конфиги (4КБ - секреты не в git).
# Локально 14 дней + rsync на DE-ноду как offsite внутри своей инфры.
set -euo pipefail

BASE=/opt/proliv
DIR=$BASE/backups
DATE=$(date +%F)
DEST=$DIR/$DATE
OFFSITE_HOST=13.143.192.49
OFFSITE_DIR=/root/proliv-backups

mkdir -p "$DEST"
chmod 700 "$DIR" "$DEST"

# --- remnawave panel DB ---
docker exec remnawave-db pg_dump -U postgres -d postgres --format=custom -f /tmp/panel.dump
docker cp remnawave-db:/tmp/panel.dump "$DEST/panel.dump"
docker exec remnawave-db rm -f /tmp/panel.dump

# --- minishop DB ---
docker exec remnawave-minishop-postgres pg_dump -U remnawave_minishop -d remnawave_minishop --format=custom -f /tmp/shop.dump
docker cp remnawave-minishop-postgres:/tmp/shop.dump "$DEST/shop.dump"
docker exec remnawave-minishop-postgres rm -f /tmp/shop.dump

# --- конфиги (секреты - perms 600; ~4КБ, env не в git) ---
tar czf "$DEST/configs.tar.gz" -C "$BASE" proliv.env shop/.env docker-compose.yml 2>/dev/null || true

chmod 600 "$DEST"/*

# ретенция 14 дней
find "$DIR" -mindepth 1 -maxdepth 1 -type d -mtime +14 -exec rm -rf {} +

# offsite-копия на DE-ноду (если настроен ключ)
if [ -f /root/.ssh/backup_ed25519 ]; then
  rsync -a --delete -e "ssh -i /root/.ssh/backup_ed25519 -o BatchMode=yes -o StrictHostKeyChecking=accept-new" \
    "$DIR/" "root@$OFFSITE_HOST:$OFFSITE_DIR/" || echo "WARN: offsite rsync failed"
fi

echo "backup done: $DEST ($(du -sh "$DEST" | cut -f1))"
