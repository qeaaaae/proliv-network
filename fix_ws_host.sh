#!/usr/bin/env bash
set -uo pipefail
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
H=(-H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' -H 'X-Forwarded-Proto: https' -H 'Content-Type: application/json')

python3 - <<'PY' > /tmp/cp_patch2.json
import json
d=json.load(open('/tmp/cp_full.json'))
r=d.get('response',d)
cfg=r['config']
for ib in cfg['inbounds']:
    if ib['tag']=='VLESS-WS-CDN':
        ib['streamSettings']['wsSettings']['host']=''
body={"uuid":r['uuid'],"name":r['name'],"config":cfg}
print(json.dumps(body))
PY
curl -s -X PATCH "${H[@]}" --data @/tmp/cp_patch2.json "$API/config-profiles" | python3 -c "import json,sys;d=json.load(sys.stdin);print('ok' if d.get('response') else d)"
sleep 4
ssh root@13.143.192.49 "docker exec remnanode tail -3 /var/log/xray/current" 2>/dev/null || true
