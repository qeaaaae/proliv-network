#!/usr/bin/env bash
set -euo pipefail
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
H=(-H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' -H 'X-Forwarded-Proto: https')

curl -s "${H[@]}" "$API/hosts" -o /tmp/hosts.json
python3 - <<'PY'
import json
d=json.load(open('/tmp/hosts.json'))
r=d.get('response',d) if isinstance(d,dict) else d
hosts=r.get('hosts',r.get('items')) if isinstance(r,dict) else r
for h in hosts:
    print(h.get('uuid'),'|',repr(h.get('remark')),'|',h.get('address'),':',h.get('port'))
PY

python3 - <<'PY'
import json
d=json.load(open('/tmp/hosts.json'))
r=d.get('response',d) if isinstance(d,dict) else d
hosts=r.get('hosts',r.get('items')) if isinstance(r,dict) else r
target=[h for h in hosts if h.get('address')=='ee.proliv-network.xyz']
if not target:
    target=[h for h in hosts if 'CDN' in str(h.get('remark'))]
u=target[0]['uuid']
body={"uuid":u,"remark":"🇪🇪 LTE Эстония (Моб. Интернет)"}
open('/tmp/host_patch.json','w').write(json.dumps(body,ensure_ascii=False))
print('patch host:',u)
PY

echo "--- PATCH ---"
curl -s -X PATCH "${H[@]}" -H 'Content-Type: application/json' --data-binary @/tmp/host_patch.json "$API/hosts" | head -c 400
echo
echo "=== verify ==="
curl -s "${H[@]}" "$API/hosts" -o /tmp/hosts2.json
python3 - <<'PY'
import json
d=json.load(open('/tmp/hosts2.json'))
r=d.get('response',d) if isinstance(d,dict) else d
hosts=r.get('hosts',r.get('items')) if isinstance(r,dict) else r
for h in hosts:
    print(h.get('uuid'),'|',repr(h.get('remark')),'|',h.get('address'))
PY
