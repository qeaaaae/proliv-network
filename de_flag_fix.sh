#!/usr/bin/env bash
set -uo pipefail
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
H=(-H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' -H 'X-Forwarded-Proto: https' -H 'Content-Type: application/json')
curl -s -X PATCH "${H[@]}" --data '{"uuid":"94a4ca12-7b38-4f87-9cdb-eea87a77511a","remark":"🇩🇪 ⚡ Германия"}' "$API/hosts" | python3 -c "import json,sys;print(json.load(sys.stdin)['response']['remark'])"
curl -s -D - -o /dev/null -A 'Happ/5.8.0/ios/2609081608581' 'http://127.0.0.1:3444/WKA2c2STkbrb5LHf' | grep -i 'subscription-userinfo'
