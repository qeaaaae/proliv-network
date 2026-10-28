#!/usr/bin/env bash
set -uo pipefail
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
H=(-H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' -H 'X-Forwarded-Proto: https' -H 'Content-Type: application/json')
curl -s -X PATCH "${H[@]}" "$API/users" --data '{"username":"raf","trafficLimitBytes":0,"trafficLimitStrategy":"NO_RESET","hwidDeviceLimit":10}' -o /tmp/ru_resp.json
head -c 400 /tmp/ru_resp.json; echo
python3 - <<'PY'
import json
d=json.load(open('/tmp/ru_resp.json'))
if 'response' not in d: raise SystemExit(0)
u=d['response']
print(u['username'],'| traffic limit:',u.get('trafficLimitBytes'),'(0 = безлимит) | strategy:',u.get('trafficLimitStrategy'),'| devices:',u.get('hwidDeviceLimit'),'| expire:',u.get('expireAt'),'| status:',u.get('status'))
PY
exit 0
python3 -c "
import json,sys
u=json.load(sys.stdin)['response']
print(u['username'],'| traffic limit:',u.get('trafficLimitBytes'),'(0 = безлимит) | strategy:',u.get('trafficLimitStrategy'),'| devices:',u.get('hwidDeviceLimit'),'| expire:',u.get('expireAt'),'| status:',u.get('status'))
"
