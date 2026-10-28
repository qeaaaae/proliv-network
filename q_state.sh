#!/usr/bin/env bash
set -uo pipefail
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
H=(-H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' -H 'X-Forwarded-Proto: https' -H 'Content-Type: application/json')

echo "=== HOSTS keys ==="
curl -s "${H[@]}" "$API/hosts" > /tmp/hosts.json
python3 -c '
import json
d=json.load(open("/tmp/hosts.json"))
r=d["response"]
print(type(r), list(r.keys()) if isinstance(r,dict) else len(r))
hosts = r["hosts"] if isinstance(r,dict) and "hosts" in r else r
for h in hosts:
    print(json.dumps({k:h.get(k) for k in ("uuid","remark","address","port","isDisabled","viewPosition")},ensure_ascii=False))
'

echo "=== USERS raw ==="
curl -s "${H[@]}" "$API/users" > /tmp/users.json
python3 -c '
import json
d=json.load(open("/tmp/users.json"))
r=d["response"]
users=r["users"] if isinstance(r,dict) else r
print("count:",len(users))
for u in users:
    print(json.dumps(u,ensure_ascii=False)[:600])
'
