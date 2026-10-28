#!/usr/bin/env bash
set -uo pipefail
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
H=(-H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' -H 'X-Forwarded-Proto: https' -H 'Content-Type: application/json')

# ---------- 1. Fix XRAY_JSON template ----------
python3 - <<'PY' > /tmp/tpl_patch.json
import json
tpl={
 "dns":{"servers":["77.88.8.8","77.88.8.1","1.1.1.1"],"queryStrategy":"UseIP"},
 "routing":{
  "rules":[
   {"type":"field","domain":["geosite:category-ru"],"outboundTag":"direct"},
   {"type":"field","ip":["geoip:private"],"outboundTag":"direct"},
   {"type":"field","protocol":["bittorrent"],"outboundTag":"direct"}
  ],
  "domainMatcher":"hybrid","domainStrategy":"AsIs"
 },
 "inbounds":[
  {"tag":"socks","port":10808,"listen":"127.0.0.1","protocol":"socks","settings":{"udp":True,"auth":"noauth"},"sniffing":{"enabled":True,"routeOnly":False,"destOverride":["http","tls","quic"]}},
  {"tag":"http","port":10809,"listen":"127.0.0.1","protocol":"http","settings":{"allowTransparent":False},"sniffing":{"enabled":True,"routeOnly":False,"destOverride":["http","tls","quic"]}}
 ],
 "outbounds":[
  {"tag":"direct","protocol":"freedom"},
  {"tag":"block","protocol":"blackhole"}
 ]
}
print(json.dumps({"uuid":"3a575487-4b1d-47da-901e-9e928254385a","templateJson":tpl}))
PY
curl -s -X PATCH "${H[@]}" --data @/tmp/tpl_patch.json "$API/subscription-templates" | head -c 300; echo

# ---------- 2. sockopt fragment on reality hosts ----------
curl -s "${H[@]}" "$API/hosts" -o /tmp/hosts.json
python3 - <<'PY' > /tmp/host_patches.txt
import json
d=json.load(open('/tmp/hosts.json'))
r=d.get('response',d) if isinstance(d,dict) else d
hosts=r.get('hosts',r.get('items')) if isinstance(r,dict) else r
for h in hosts:
    a=h.get('address','')
    if a.endswith('proliv-network.xyz') and 'ee.proliv' not in a:
        print(h['uuid'],a)
PY
cat /tmp/host_patches.txt
while read -r uuid addr; do
  python3 - <<PY > /tmp/hp.json
import json
print(json.dumps({"uuid":"$uuid","sockoptParams":{"fragment":{"packets":"tlshello","length":"50-150","interval":"10-50"}}}))
PY
  echo "--- PATCH $addr"
  curl -s -X PATCH "${H[@]}" --data @/tmp/hp.json "$API/hosts" | head -c 200; echo
done < /tmp/host_patches.txt

# ---------- 3. response rules: add Happ/Incy -> XRAY_JSON ----------
curl -s "${H[@]}" "$API/subscription-settings" -o /tmp/ss.json
python3 - <<'PY' > /tmp/rr.json
import json
d=json.load(open('/tmp/ss.json'))
r=d.get('response',d)
rules=r['responseRules']['rules']
new={"name":"Happ/Incy (xray json)","enabled":True,"operator":"AND",
 "conditions":[{"value":"^(happ|incy)","operator":"REGEX","headerName":"user-agent","caseSensitive":False}],
 "description":"Full xray config with fixed routing+fragment","responseType":"XRAY_JSON"}
# insert before fallback (last rule with empty conditions)
pos=len(rules)
for i,r_ in enumerate(rules):
    if not r_.get('conditions'):
        pos=i; break
rules.insert(pos,new)
r['responseRules']['rules']=rules
body={k:v for k,v in r.items() if k in ('uuid','serveJsonAtBaseSubscription','isShowCustomRemarks','customRemarks','customResponseHeaders','randomizeHosts','responseRules')}
print(json.dumps(body,ensure_ascii=False))
PY
curl -s -X PATCH "${H[@]}" --data @/tmp/rr.json "$API/subscription-settings" | head -c 300; echo
echo "=== verify rules ==="
curl -s "${H[@]}" "$API/subscription-settings" | python3 -c "import json,sys;d=json.load(sys.stdin);r=d['response'];[print(x['name'],'->',x['responseType'],'| enabled:',x['enabled']) for x in r['responseRules']['rules']]"
