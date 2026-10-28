#!/usr/bin/env bash
set -uo pipefail
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
H=(-H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' -H 'Content-Type: application/json')

curl -s "${H[@]}" "$API/hosts" | python3 -c "
import json,sys
d=json.load(sys.stdin)
for h in d['response']:
    r=h['remark']
    if 'TEST-IP' in r or '(WS)' in r:
        print(h['uuid'],r)
" > /tmp/del.txt
cat /tmp/del.txt
while read -r u rest; do
  curl -s -X DELETE "${H[@]}" "$API/hosts/$u" -o /dev/null
done < /tmp/del.txt
echo '=== remaining ==='
curl -s "${H[@]}" "$API/hosts" | python3 -c "import json,sys;[print(h['remark']) for h in json.load(sys.stdin)['response']]"
