#!/usr/bin/env bash
set -uo pipefail
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
H=(-H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' -H 'X-Forwarded-Proto: https')

echo "=== config profile inbounds ==="
curl -s "${H[@]}" "$API/config-profiles" -o /tmp/cp.json
python3 - <<'PY'
import json
d=json.load(open('/tmp/cp.json'))
r=d.get('response',d)
ps=r.get('configProfiles',r if isinstance(r,list) else r.get('items',[]))
for p in ps:
    print('profile:',p.get('uuid'),'|',p.get('name'))
    cfg=p.get('config',{})
    for ib in cfg.get('inbounds',[]):
        print(json.dumps(ib,ensure_ascii=False)[:600])
PY

echo
echo "=== EE CDN host full ==="
curl -s "${H[@]}" "$API/hosts" -o /tmp/hosts.json
python3 - <<'PY'
import json
d=json.load(open('/tmp/hosts.json'))
r=d.get('response',d) if isinstance(d,dict) else d
hosts=r.get('hosts',r.get('items')) if isinstance(r,dict) else r
for h in hosts:
    if h.get('address')=='ee.proliv-network.xyz':
        print(json.dumps(h,ensure_ascii=False,indent=1))
PY

echo
echo "=== EE node ==="
curl -s "${H[@]}" "$API/nodes" -o /tmp/nodes.json
python3 - <<'PY'
import json
d=json.load(open('/tmp/nodes.json'))
r=d.get('response',d)
nodes=r.get('items',r.get('nodes',r if isinstance(r,list) else []))
for n in nodes:
    if 'ee' in str(n.get('name','')).lower() or 'эстон' in str(n.get('name','')):
        print(json.dumps(n,ensure_ascii=False,indent=1)[:2500])
PY
