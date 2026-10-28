#!/usr/bin/env bash
set -uo pipefail
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
H=(-H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' -H 'X-Forwarded-Proto: https' -H 'Content-Type: application/json')

curl -s "${H[@]}" "$API/config-profiles/00000000-0000-0000-0000-000000000000" -o /tmp/cp3.json
XUUID=$(python3 -c "import json;d=json.load(open('/tmp/cp3.json'));r=d['response'];print([i['uuid'] for i in r['inbounds'] if i['tag']=='VLESS-XHTTP-CDN'][0])")
WSUUID=$(python3 -c "import json;d=json.load(open('/tmp/cp3.json'));r=d['response'];print([i['uuid'] for i in r['inbounds'] if i['tag']=='VLESS-WS-CDN'][0])")
echo "XHTTP ib: $XUUID | WS ib: $WSUUID"

# repoint LTE host to xhttp inbound (restore binding)
python3 - <<PY > /tmp/lte_fix.json
import json
print(json.dumps({"uuid":"499f8118-d8a0-49f2-becf-9627c0069fb8",
 "inbound":{"configProfileUuid":"00000000-0000-0000-0000-000000000000","configProfileInboundUuid":"$XUUID"}}))
PY
curl -s -X PATCH "${H[@]}" --data @/tmp/lte_fix.json "$API/hosts" | python3 -c "import json,sys;d=json.load(sys.stdin);r=d.get('response',d);print('LTE inbound now:',r.get('inbound'))"

# also verify ws-8444 hosts still bound correctly
curl -s "${H[@]}" "$API/hosts" | python3 -c "
import json,sys
d=json.load(sys.stdin);r=d.get('response',d)
hosts=r.get('hosts',r.get('items')) if isinstance(r,dict) else r
for h in hosts:
    if h.get('port')==8444:
        print(h['remark'],'| inbound:',(h.get('inbound') or {}).get('configProfileInboundUuid'))
"
