#!/usr/bin/env bash
set -uo pipefail
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
H=(-H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' -H 'X-Forwarded-Proto: https')
echo "=== subscription-settings (rules) ==="
curl -s "${H[@]}" "$API/subscription-settings" -o /tmp/ss.json
python3 - <<'PY'
import json
d=json.load(open('/tmp/ss.json'))
r=d.get('response',d)
print(json.dumps(r,ensure_ascii=False,indent=1)[:4000])
PY
echo "=== sockoptParams schema in contract ==="
F=/var/lib/docker/rootfs/overlayfs/9743afaecf0ed3f2d6cf96a7fc4943ca69c10c16f71243224a9072593ea2d4b3/opt/app/dist
grep -rhoE "sockoptParams[^;,]{0,300}" $F/app.js 2>/dev/null | head -5
