#!/usr/bin/env bash
set -u
echo "=== containers ==="
docker ps --format '{{.Names}}\t{{.Image}}' | grep -iE 'minishop|postgres|shop|backend' || docker ps --format '{{.Names}}'

BE="$(docker ps --format '{{.Names}}' | grep -iE 'backend' | head -1)"
PG="$(docker ps --format '{{.Names}}' | grep -iE 'postgres' | head -1)"
echo "BE=$BE PG=$PG"

echo "=== backend env hwid/device ==="
if [ -n "$BE" ]; then docker exec "$BE" printenv | grep -E '^(USER_HWID_DEVICE_LIMIT|TRIAL_HWID_DEVICE_LIMIT|.*HWID.*)=' || echo "(no HWID env vars)"; fi

echo "=== env file keys (names only) ==="
for f in /opt/proliv/shop/.env /opt/proliv/.env /opt/proliv/proliv.env; do
  if [ -f "$f" ]; then echo "--- $f"; grep -nE 'HWID|DEVICE_LIMIT' "$f" | sed -E 's/=(.*)/=<set>/' || true; fi
done

echo "=== subscriptions ==="
if [ -n "$PG" ]; then
docker exec -i "$PG" psql -U remnawave_minishop -d remnawave_minishop -c \
"select subscription_id, user_id, provider, tariff_key, hwid_device_limit, hwid_device_limit_is_override, extra_hwid_devices, is_active, status_from_panel from subscriptions order by subscription_id desc limit 15;"
fi

echo "=== tariffs table ==="
if [ -n "$PG" ]; then
docker exec -i "$PG" psql -U remnawave_minishop -d remnawave_minishop -c \
"select key, hwid_device_limit from tariffs limit 10;" 2>/dev/null || echo "(no tariffs table)"
fi
