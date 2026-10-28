#!/usr/bin/env bash
set -uo pipefail
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
H=(-H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' -H 'X-Forwarded-Proto: https')
curl -s "${H[@]}" "$API/users?size=50&start=0" | python3 -c "
import json,sys
d=json.load(sys.stdin)['response']
for u in d.get('users',[]):
    print(u.get('username'),'| id:',u.get('id'),'| expire:',u.get('expireAt'),'| limit:',u.get('trafficLimitBytes'),'| hwid:',u.get('hwidDeviceLimit'),'| status:',u.get('status'),'| url:',u.get('subscriptionUrl'))
"
