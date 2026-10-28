#!/usr/bin/env bash
set -uo pipefail
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
curl -s -H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' "$API/config-profiles/00000000-0000-0000-0000-000000000000" | python3 -c "
import json,sys
p=json.load(sys.stdin)['response']
for i in p.get('inbounds',[]):
    print('===',i['tag'])
    print(json.dumps(i,ensure_ascii=False,indent=1)[:2500])
"
