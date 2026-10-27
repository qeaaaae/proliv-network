#!/bin/bash
# Query Remnawave panel API via devproxy bridge (injects X-Forwarded headers).
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"

echo "=== config-profiles ==="
curl -s -o /tmp/profiles.json -H "Authorization: Bearer $JWT" "$API/config-profiles"
python3 - <<'PY'
import json
d = json.load(open('/tmp/profiles.json'))
profiles = d.get('response', d)
if isinstance(profiles, dict):
    profiles = profiles.get('configProfiles', profiles.get('items', profiles))
for p in (profiles if isinstance(profiles, list) else []):
    print(p.get('uuid'), '|', p.get('name'))
PY

echo "=== nodes ==="
curl -s -o /tmp/nodes.json -H "Authorization: Bearer $JWT" "$API/nodes"
python3 - <<'PY'
import json
d = json.load(open('/tmp/nodes.json'))
nodes = d.get('response', d)
if isinstance(nodes, dict):
    nodes = nodes.get('items', nodes.get('nodes', nodes))
for n in (nodes if isinstance(nodes, list) else []):
    print(n.get('uuid'), '|', n.get('name'), '|', n.get('address'), '|profile:', (n.get('configProfile') or {}))
PY
