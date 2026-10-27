#!/bin/bash
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
curl -s -o /tmp/ee_node.json -H "Authorization: Bearer $JWT" "$API/nodes/c0ad1fb9-a8f0-469d-aafb-a3be7763d45f"
python3 - <<'PY'
import json
d = json.load(open('/tmp/ee_node.json'))
n = d.get('response', d)
# print all top-level fields except bulky ones
for k, v in n.items():
    if k in ('configProfile',):
        continue
    print(k, '=', json.dumps(v)[:300])
PY
