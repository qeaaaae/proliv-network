#!/usr/bin/env bash
set -euo pipefail
cd /opt/proliv
sed -i 's/\r$//' infra/status-probe.py infra/ipregion-node-install.sh
python3 infra/status-probe.py
python3 - <<'PY'
import json
d = json.load(open('/opt/proliv/status/status.json'))
for l in d['groups']['locations']:
    g = l.get('geo') or {}
    print(l['name'], '| geo:', bool(g), '| YouTube:', g.get('custom', {}).get('YouTube'))
PY
docker compose -f shop/docker-compose.yml -f infra/minishop.compose.yml -f infra/minishop.prod.compose.yml --env-file shop/.env --profile bot up -d --build bot 2>&1 | tail -4
sleep 8
docker ps --format '{{.Names}} {{.Status}}' | grep -i bot
docker exec remnawave-minishop-bot python -c "from bot.handlers.admin.nodes_geo import render_location_block; print('import ok')" 2>&1 || true
