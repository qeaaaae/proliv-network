#!/usr/bin/env bash
set -uo pipefail
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
H=(-H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' -H 'X-Forwarded-Proto: https' -H 'Content-Type: application/json')

# 1. remove `routing` custom header (keep the rest)
curl -s "${H[@]}" "$API/subscription-settings" -o /tmp/ss2.json
python3 - <<'PY' > /tmp/rr2.json
import json
d=json.load(open('/tmp/ss2.json'))
r=d.get('response',d)
r.get('customResponseHeaders',{}).pop('routing',None)
body={k:v for k,v in r.items() if k in ('uuid','serveJsonAtBaseSubscription','isShowCustomRemarks','customRemarks','customResponseHeaders','randomizeHosts','responseRules')}
print(json.dumps(body,ensure_ascii=False))
PY
curl -s -X PATCH "${H[@]}" --data @/tmp/rr2.json "$API/subscription-settings" | python3 -c "import json,sys;d=json.load(sys.stdin);r=d.get('response',d);print('headers now:',list(r.get('customResponseHeaders',{}).keys()))"

# 2. delete reserve hosts
for uuid in d406e85b-294c-4316-af39-5baacd87cb66 0166a459-a6f9-400e-b8f7-bc35fb028e4e 62027def-6ac5-4d41-8a20-6ad3aa380227; do
  curl -s -X DELETE "${H[@]}" "$API/hosts/$uuid" -o /dev/null && echo "deleted $uuid"
done
