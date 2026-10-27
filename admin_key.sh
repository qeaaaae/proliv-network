#!/usr/bin/env bash
set -euo pipefail
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
H=(-H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' -H 'X-Forwarded-Proto: https')

echo "=== delete old panel users by id ==="
for id in $(python3 -c "
import json
d=json.load(open('/tmp/panel_users.json'))
r=d.get('response',d)
us=r.get('users',r if isinstance(r,list) else r.get('items',[]))
print(' '.join(str(u.get('id')) for u in us if u.get('id') is not None))
"); do
  echo "-- DELETE /users/$id"
  curl -s -X DELETE "${H[@]}" "$API/users/$id"; echo
done

echo "=== users after ==="
curl -s "${H[@]}" "$API/users?size=100" | python3 -c "
import json,sys
d=json.load(sys.stdin)
r=d.get('response',d)
us=r.get('users',r if isinstance(r,list) else r.get('items',[]))
print('count:',len(us))
for u in us: print(u.get('id'),'|',u.get('username'))
"

echo "=== create admin key ==="
cat > /tmp/newuser.json <<'JSON'
{
  "username": "raf",
  "status": "ACTIVE",
  "expireAt": "2100-01-01T00:00:00.000Z",
  "trafficLimitBytes": 0,
  "trafficLimitStrategy": "NO_RESET",
  "hwidDeviceLimit": 10,
  "telegramId": 880994961,
  "activeInternalSquads": ["2b5f5dcd-0099-4f51-bc26-0ba04c240d63"],
  "description": "owner admin key"
}
JSON
curl -s -X POST "${H[@]}" -H 'Content-Type: application/json' -d @/tmp/newuser.json "$API/users" -o /tmp/newuser_resp.json
python3 - <<'PY'
import json
d=json.load(open('/tmp/newuser_resp.json'))
r=d.get('response',d)
if 'username' not in r:
    print('RAW:', json.dumps(d)[:1500])
else:
    print('username:', r.get('username'))
    print('id:', r.get('id'))
    print('status:', r.get('status'))
    print('expireAt:', r.get('expireAt'))
    print('trafficLimitBytes:', r.get('trafficLimitBytes'))
    print('hwidDeviceLimit:', r.get('hwidDeviceLimit'))
    print('telegramId:', r.get('telegramId'))
    print('SUBSCRIPTION_URL:', r.get('subscriptionUrl'))
PY
