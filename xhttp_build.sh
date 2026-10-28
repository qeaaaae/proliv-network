#!/usr/bin/env bash
set -uo pipefail
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
H=(-H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' -H 'X-Forwarded-Proto: https')

echo "=== full config profile ==="
curl -s "${H[@]}" "$API/config-profiles/00000000-0000-0000-0000-000000000000" -o /tmp/cp_full.json
python3 - <<'PY'
import json
d=json.load(open('/tmp/cp_full.json'))
r=d.get('response',d)
print('keys:',list(r.keys()))
cfg=r.get('config') or r.get('configProfile') or {}
print(json.dumps(r,ensure_ascii=False)[:300])
PY
