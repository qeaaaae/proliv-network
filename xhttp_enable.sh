#!/usr/bin/env bash
set -uo pipefail
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
H=(-H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' -H 'X-Forwarded-Proto: https' -H 'Content-Type: application/json')
XIB="2c993132-0ecf-4a7d-9692-5259aa325d5e"

echo "=== nodes ==="
curl -s "${H[@]}" "$API/nodes" -o /tmp/nodes.json
python3 - <<'PY'
import json
d=json.load(open('/tmp/nodes.json'))
r=d.get('response',d)
nodes=r if isinstance(r,list) else r.get('items',r.get('nodes',[]))
for n in nodes:
    nm=n.get('name','')
    print(nm, n.get('uuid'), '| activeInbounds:', [i.get('tag') or i for i in (n.get('activeInbounds') or n.get('configProfile',{}).get('activeConfigProfileInbounds') or [])])
    if 'EE' in nm or 'стон' in nm or 'ee' in nm.lower():
        print('EE NODE FULL:', json.dumps(n,ensure_ascii=False)[:1500])
PY
