#!/bin/bash
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"

echo "=== Default-Profile full config ==="
curl -s -o /tmp/profile.json -H "Authorization: Bearer $JWT" "$API/config-profiles/00000000-0000-0000-0000-000000000000"
python3 - <<'PY'
import json
d = json.load(open('/tmp/profile.json'))
print(json.dumps(d, indent=1)[:6000])
PY
