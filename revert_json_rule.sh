#!/usr/bin/env bash
set -uo pipefail
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
H=(-H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' -H 'X-Forwarded-Proto: https' -H 'Content-Type: application/json')

curl -s "${H[@]}" "$API/subscription-settings" -o /tmp/ss3.json
python3 - <<'PY' > /tmp/rr3.json
import json
d=json.load(open('/tmp/ss3.json'))
r=d.get('response',d)
rules=[x for x in r['responseRules']['rules'] if x['name']!='Happ/Incy (xray json)']
r['responseRules']['rules']=rules
body={k:v for k,v in r.items() if k in ('uuid','serveJsonAtBaseSubscription','isShowCustomRemarks','customRemarks','customResponseHeaders','randomizeHosts','responseRules')}
print(json.dumps(body,ensure_ascii=False))
PY
curl -s -X PATCH "${H[@]}" --data @/tmp/rr3.json "$API/subscription-settings" | python3 -c "import json,sys;d=json.load(sys.stdin);r=d.get('response',d);[print(x['name'],'->',x['responseType']) for x in r['responseRules']['rules']]"
