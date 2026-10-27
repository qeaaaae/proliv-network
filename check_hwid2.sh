#!/usr/bin/env bash
set -u
echo "=== tariffs.json in backend container ==="
docker exec remnawave-minishop-backend sh -c 'ls -la /app/data/ | grep -iE "tariff|json"; echo ---; python -c "import json,sys; d=json.load(open(\"/app/data/tariffs.json\")); print(json.dumps(d,ensure_ascii=False)[:3000])" 2>/dev/null || cat /app/data/tariffs.json | head -80'
echo
echo "=== same in bot container ==="
docker exec remnawave-minishop-bot sh -c 'md5sum /app/data/tariffs.json 2>/dev/null; python -c "import json; d=json.load(open(\"/app/data/tariffs.json\")); print([t.get(\"hwid_device_limit\") for t in (d.get(\"tariffs\") or d if isinstance(d,list) else d.get(\"tariffs\",[]))])" 2>/dev/null' 2>/dev/null || true
