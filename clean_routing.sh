#!/usr/bin/env bash
set -uo pipefail
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
H=(-H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' -H 'Content-Type: application/json')

# clean routing profile for Happ (base64 in customResponseHeaders.routing)
python3 - <<'PY' > /tmp/routing_b64.txt
import json,base64
r={
 "name":"Proliv",
 "domainStrategy":"AsIs",
 "rules":[
   {"type":"field","domain":["geosite:category-ru"],"outboundTag":"direct"},
   {"type":"field","ip":["geoip:private","geoip:ru"],"outboundTag":"direct"},
   {"type":"field","network":"tcp,udp","outboundTag":"proxy"}
 ]
}
print(base64.b64encode(json.dumps(r).encode()).decode())
PY

curl -s "${H[@]}" "$API/subscription-settings" -o /tmp/ss.json
python3 - <<'PY' > /tmp/ssp.json
import json
d=json.load(open('/tmp/ss.json'))
r=d.get('response',d)
b64=open('/tmp/routing_b64.txt').read().strip()
crh=r.get('customResponseHeaders') or {}
crh['routing']='rwEncodeBase64:'+b64 if not b64.startswith('rwEncode') else b64
crh['routing']=b64
r['customResponseHeaders']=crh
body={k:v for k,v in r.items() if k in ('uuid','serveJsonAtBaseSubscription','isShowCustomRemarks','customRemarks','customResponseHeaders','randomizeHosts','responseRules')}
print(json.dumps(body,ensure_ascii=False))
PY
curl -s -X PATCH "${H[@]}" --data @/tmp/ssp.json "$API/subscription-settings" | python3 -c "import json,sys;d=json.load(sys.stdin);r=d.get('response',d);print('headers:',list((r.get('customResponseHeaders') or {}).keys()))"
