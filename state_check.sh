#!/usr/bin/env bash
set -uo pipefail
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
H=(-H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1')

echo '=== PROFILE INBOUNDS ==='
curl -s "${H[@]}" "$API/config-profiles/00000000-0000-0000-0000-000000000000" | python3 -c "import json,sys;d=json.load(sys.stdin);r=d.get('response',d);[print(i.get('tag'),'|',i.get('uuid')) for i in r.get('inbounds',[])]"
echo '=== NODES ==='
curl -s "${H[@]}" "$API/nodes" | python3 -c "import json,sys;d=json.load(sys.stdin);[print(n['name'],'|',[i.get('tag') for i in n.get('activeInbounds',[])]) for n in d['response']]"
echo '=== HOSTS ==='
curl -s "${H[@]}" "$API/hosts" | python3 -c "import json,sys;d=json.load(sys.stdin);[print(h['remark'],'|',h['address'],h['port'],h.get('path'),'|sockopt:',h.get('sockoptParams'),'|inb:',(h.get('inbound') or {}).get('configProfileInboundUuid')) for h in d['response']]"
