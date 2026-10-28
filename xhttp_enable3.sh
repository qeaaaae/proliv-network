#!/usr/bin/env bash
set -uo pipefail
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
H=(-H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' -H 'X-Forwarded-Proto: https' -H 'Content-Type: application/json')
XIB="2c993132-0ecf-4a7d-9692-5259aa325d5e"
EE="c0ad1fb9-a8f0-469d-aafb-a3be7763d45f"
PROF="00000000-0000-0000-0000-000000000000"

# update node update schema quickly
U=/var/lib/docker/rootfs/overlayfs/9743afaecf0ed3f2d6cf96a7fc4943ca69c10c16f71243224a9072593ea2d4b3/opt/app/dist/node_modules/@remnawave/backend-contract/build/backend/commands/nodes/update.command.js
grep -oE 'RequestBodySchema[^;]{0,900}' "$U" | head -3

echo "=== patch EE node inbounds ==="
python3 - <<'PY' > /tmp/node_patch.json
import json
print(json.dumps({"uuid":"c0ad1fb9-a8f0-469d-aafb-a3be7763d45f","configProfile":{"activeConfigProfileUuid":"00000000-0000-0000-0000-000000000000","activeInbounds":["010eeb5a-4c4d-4bbe-9bec-390ab735b363","d7b7bf74-239a-45d4-bfdc-b025eb1fa0b6","2c993132-0ecf-4a7d-9692-5259aa325d5e"]}}))
PY
cat /tmp/node_patch.json; echo
curl -s -X PATCH "${H[@]}" --data @/tmp/node_patch.json "$API/nodes" | python3 -c "import json,sys;d=json.load(sys.stdin);r=d.get('response',d);print('inbounds now:',[i['tag'] for i in r.get('configProfile',{}).get('activeInbounds',[])])"

echo "=== squads ==="
curl -s "${H[@]}" "$API/internal-squads" -o /tmp/sq.json
python3 - <<'PY'
import json
d=json.load(open('/tmp/sq.json'))
r=d.get('response',d)
sq=r if isinstance(r,list) else r.get('items',[])
for s in sq:
    print(s.get('name'),s.get('uuid'),'| inbounds:',[i.get('tag') for i in s.get('inbounds',[])])
PY
