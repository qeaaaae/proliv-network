#!/usr/bin/env bash
set -uo pipefail
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
H=(-H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1')

curl -s "${H[@]}" "$API/config-profiles/00000000-0000-0000-0000-000000000000" | python3 -c "
import json,sys
p=json.load(sys.stdin)['response']
for i in p.get('inbounds',[]):
    print(i['tag'],'| ws:',i.get('wsSettings'),'| reality keys:',[k for k in i.keys() if 'reality' in k.lower() or 'dest' in k.lower()])
"
echo '=== SUB HEADERS ==='
curl -s -A 'Happ/5.8.0/ios/2609081608581' -D- -o /tmp/sub.txt 'http://127.0.0.1:3444/WKA2c2STkbrb5LHf' | grep -iE 'HTTP/|routing|profile|content-type'
echo '=== SUB LINKS ==='
base64 -d /tmp/sub.txt 2>/dev/null | grep vless
