#!/bin/bash
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
curl -s -o /tmp/hosts.json -H "Authorization: Bearer $JWT" "$API/hosts"
python3 - <<'PY'
import json
d = json.load(open('/tmp/hosts.json'))
print(json.dumps(d, indent=1)[:8000])
PY
