#!/usr/bin/env bash
set -u
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
H=(-H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' -H 'X-Forwarded-Proto: https')

echo "=== raf user state ==="
curl -s "${H[@]}" "$API/users?size=100" -o /tmp/u.json
python3 - <<'PY'
import json
d=json.load(open('/tmp/u.json'))
r=d.get('response',d)
us=r.get('users',r if isinstance(r,list) else r.get('items',[]))
for u in us:
    print('id',u.get('id'),'|',u.get('username'),'|',u.get('status'))
    ut=u.get('userTraffic') or {}
    print('  used:',ut.get('usedTrafficBytes'),'lifetime:',ut.get('lifetimeUsedTrafficBytes'))
    print('  onlineAt:',ut.get('onlineAt'),'lastNode:',ut.get('lastConnectedNodeUuid'))
    print('  vlessUuid:',u.get('vlessUuid'))
PY

echo
echo "=== DE node xray log: last activity ==="
ssh proliv-node-de "docker exec remnanode tail -40 /var/log/xray/current 2>/dev/null | grep -vE '^\s*$' | tail -25" 2>/dev/null || echo "(ssh de fail)"

echo
echo "=== UK node xray log ==="
ssh proliv-node-uk "docker exec remnanode tail -30 /var/log/xray/current 2>/dev/null | tail -15" 2>/dev/null || echo "(ssh uk fail)"

echo
echo "=== EE node xray log ==="
ssh proliv-node-ee "docker exec remnanode tail -30 /var/log/xray/current 2>/dev/null | tail -15" 2>/dev/null || echo "(ssh ee fail)"
