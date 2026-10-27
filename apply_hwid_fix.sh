#!/usr/bin/env bash
set -euo pipefail

echo "=== write overrides ==="
docker exec -i remnawave-minishop-postgres psql -U remnawave_minishop -d remnawave_minishop <<'SQL'
INSERT INTO app_setting_overrides (key, value, updated_at, updated_by)
VALUES
  ('USER_HWID_DEVICE_LIMIT', '5', NOW(), NULL),
  ('TRIAL_HWID_DEVICE_LIMIT', '5', NOW(), NULL)
ON CONFLICT (key) DO UPDATE
  SET value = EXCLUDED.value, updated_at = NOW(), updated_by = NULL;

SELECT key, value, updated_at FROM app_setting_overrides
WHERE key IN ('USER_HWID_DEVICE_LIMIT', 'TRIAL_HWID_DEVICE_LIMIT');
SQL

echo "=== restart shop services ==="
docker restart remnawave-minishop-backend remnawave-minishop-bot remnawave-minishop-worker
sleep 12

echo "=== override application in logs ==="
for c in remnawave-minishop-backend remnawave-minishop-bot remnawave-minishop-worker; do
  echo "--- $c"
  docker logs --tail 60 "$c" 2>&1 | grep -iE "override|HWID" | tail -5 || echo "(no override lines)"
done

echo "=== verify resolved settings inside backend ==="
docker exec remnawave-minishop-backend python -c "
import asyncio
from config.settings import Settings
from bot.services.settings_override_service import apply_overrides
from db.dal.app_settings_dal import get_all_overrides
from db.session import async_session_factory
async def main():
    s = Settings()
    async with async_session_factory() as sess:
        ov = await get_all_overrides(sess)
    n = apply_overrides(s, ov)
    print('overrides applied:', n)
    print('USER_HWID_DEVICE_LIMIT =', s.USER_HWID_DEVICE_LIMIT)
    print('TRIAL_HWID_DEVICE_LIMIT =', s.TRIAL_HWID_DEVICE_LIMIT)
asyncio.run(main())
" 2>&1 | tail -8
