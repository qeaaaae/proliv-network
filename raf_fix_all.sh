#!/usr/bin/env bash
set -uo pipefail
docker exec -i remnawave-minishop-postgres psql -U remnawave_minishop -d remnawave_minishop < /tmp/rsf.sql
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
H=(-H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' -H 'X-Forwarded-Proto: https' -H 'Content-Type: application/json')
curl -s -X PATCH "${H[@]}" "$API/users" --data '{"username":"raf","trafficLimitBytes":0,"trafficLimitStrategy":"NO_RESET","hwidDeviceLimit":10}' -o /dev/null
echo '=== all panel users ==='
curl -s "${H[@]}" "$API/users?size=500&start=0" | python3 -c "
import json,sys
d=json.load(sys.stdin)['response']
print('total:',d.get('total'))
for u in d['users']: print(' ',u['username'],'| limit:',u['trafficLimitBytes'],'| devices:',u['hwidDeviceLimit'],'| short:',u['shortUuid'])
"
