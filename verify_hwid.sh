#!/usr/bin/env bash
set -u
echo "=== backend startup log (overrides) ==="
docker logs remnawave-minishop-backend 2>&1 | grep -inE "override|Applied" | tail -10
echo "=== bot ==="
docker logs remnawave-minishop-bot 2>&1 | grep -inE "override|Applied" | tail -5
echo "=== worker ==="
docker logs remnawave-minishop-worker 2>&1 | grep -inE "override|Applied" | tail -5

echo "=== resolved settings inside backend container ==="
docker exec remnawave-minishop-backend python -c "
import asyncio
from config.settings import Settings
from bot.services.settings_override_service import apply_overrides
from db.dal.app_settings_dal import get_all_overrides
from db.database_setup import init_db_connection
async def main():
    s = Settings()
    sf = init_db_connection(s)
    async with sf() as sess:
        ov = await get_all_overrides(sess)
    n = apply_overrides(s, ov)
    print('overrides applied:', n)
    print('USER_HWID_DEVICE_LIMIT =', s.USER_HWID_DEVICE_LIMIT)
    print('TRIAL_HWID_DEVICE_LIMIT =', s.TRIAL_HWID_DEVICE_LIMIT)
asyncio.run(main())
" 2>&1 | tail -10
