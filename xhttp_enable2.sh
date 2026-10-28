#!/usr/bin/env bash
set -uo pipefail
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
H=(-H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' -H 'X-Forwarded-Proto: https' -H 'Content-Type: application/json')
XIB="2c993132-0ecf-4a7d-9692-5259aa325d5e"
EE="c0ad1fb9-a8f0-469d-aafb-a3be7763d45f"

# current EE inbounds
python3 - <<'PY' > /tmp/ee_ib.txt
import json
d=json.load(open('/tmp/nodes.json'))
r=d.get('response',d)
nodes=r if isinstance(r,list) else r.get('items',[])
for n in nodes:
    if n.get('name')=='EE-Node-01':
        for i in n['configProfile']['activeInbounds']:
            print(i['uuid'],i['tag'])
PY
cat /tmp/ee_ib.txt

# node update schema
grep -oE ".{50}activeInbounds.{200}" /var/lib/docker/rootfs/overlayfs/9743afaecf0ed3f2d6cf96a7fc4943ca69c10c16f71243224a9072593ea2d4b3/opt/app/dist/node_modules/@remnawave/backend-contract/build/backend/commands/nodes/*.js 2>/dev/null | head -5
find /var/lib/docker/rootfs/overlayfs/9743afaecf0ed3f2d6cf96a7fc4943ca69c10c16f71243224a9072593ea2d4b3/opt/app/dist/node_modules/@remnawave/backend-contract -name '*.js' | xargs grep -ln 'activeInbounds' | head -5
