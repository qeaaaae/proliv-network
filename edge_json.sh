#!/usr/bin/env bash
set -uo pipefail
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
H=(-H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' -H 'X-Forwarded-Proto: https' -H 'Content-Type: application/json')

echo '=== 1. fp=edge on reality hosts ==='
for hu in 94a4ca12-7b38-4f87-9cdb-eea87a77511a f5738299-a0d1-429d-9cad-3e3d261484bc ae459449-f6ed-4c52-bb66-7ca92f84b9fa; do
  curl -s -X PATCH "${H[@]}" --data "{\"uuid\":\"$hu\",\"fingerprint\":\"edge\"}" "$API/hosts" | python3 -c "import json,sys;r=json.load(sys.stdin).get('response',{});print(r.get('remark'),'| fp:',r.get('fingerprint'),'| sockopt:',r.get('sockoptParams'))"
done

echo '=== 2. delete extra hosts ==='
curl -s "${H[@]}" "$API/hosts" | python3 -c "
import json,sys
keep={'94a4ca12-7b38-4f87-9cdb-eea87a77511a','f5738299-a0d1-429d-9cad-3e3d261484bc','ae459449-f6ed-4c52-bb66-7ca92f84b9fa'}
for h in json.load(sys.stdin)['response']:
    if h['uuid'] not in keep and 'LTE' not in h['remark']:
        print(h['uuid'],h['remark'])
" > /tmp/del2.txt
cat /tmp/del2.txt
while read -r u rest; do curl -s -X DELETE "${H[@]}" "$API/hosts/$u" -o /dev/null; done < /tmp/del2.txt

echo '=== 3. xray json template (competitor-like routing) ==='
python3 - <<'PY' > /tmp/tpl2.json
import json
tpl={
 "dns":{"servers":["8.8.8.8","1.1.1.1"],"queryStrategy":"UseIP"},
 "routing":{
  "domainMatcher":"hybrid","domainStrategy":"AsIs",
  "rules":[
   {"type":"field","protocol":["quic"],"outboundTag":"block"},
   {"type":"field","protocol":["bittorrent"],"outboundTag":"direct"},
   {"type":"field","domain":["geosite:category-ru"],"outboundTag":"direct"},
   {"type":"field","ip":["geoip:private"],"outboundTag":"direct"}
  ]
 },
 "inbounds":[
  {"tag":"socks","port":10808,"listen":"127.0.0.1","protocol":"socks","settings":{"udp":True,"auth":"noauth"},"sniffing":{"enabled":True,"routeOnly":True,"destOverride":["http","tls","quic"]}},
  {"tag":"http","port":10809,"listen":"127.0.0.1","protocol":"http","settings":{"allowTransparent":False},"sniffing":{"enabled":True,"routeOnly":True,"destOverride":["http","tls","quic"]}}
 ],
 "outbounds":[{"tag":"direct","protocol":"freedom"},{"tag":"block","protocol":"blackhole"}]
}
print(json.dumps({"uuid":"3a575487-4b1d-47da-901e-9e928254385a","templateJson":tpl}))
PY
curl -s -X PATCH "${H[@]}" --data @/tmp/tpl2.json "$API/subscription-templates" | head -c 150; echo

echo '=== 4. sub settings: drop routing header, add Happ/Incy -> XRAY_JSON ==='
curl -s "${H[@]}" "$API/subscription-settings" -o /tmp/ss4.json
python3 - <<'PY' > /tmp/ss4p.json
import json
r=json.load(open('/tmp/ss4.json'))['response']
crh=r.get('customResponseHeaders') or {}
crh.pop('routing',None)
r['customResponseHeaders']=crh
rules=[x for x in r['responseRules']['rules'] if x['name']!='Happ/Incy (xray json)']
new={"name":"Happ/Incy (xray json)","enabled":True,"operator":"AND",
 "conditions":[{"value":"^(happ|incy)","operator":"REGEX","headerName":"user-agent","caseSensitive":False}],
 "description":"Full xray config, fp=edge","responseType":"XRAY_JSON"}
pos=len(rules)
for i,x in enumerate(rules):
    if not x.get('conditions'): pos=i; break
rules.insert(pos,new)
r['responseRules']['rules']=rules
body={k:v for k,v in r.items() if k in ('uuid','serveJsonAtBaseSubscription','isShowCustomRemarks','customRemarks','customResponseHeaders','randomizeHosts','responseRules')}
print(json.dumps(body,ensure_ascii=False))
PY
curl -s -X PATCH "${H[@]}" --data @/tmp/ss4p.json "$API/subscription-settings" | python3 -c "import json,sys;r=json.load(sys.stdin)['response'];print('headers:',list(r['customResponseHeaders'].keys()));[print(' ',x['name'],'->',x['responseType']) for x in r['responseRules']['rules']]"

echo '=== 5. verify what Happ gets ==='
curl -s -A 'Happ/5.8.0/ios/2609081608581' 'http://127.0.0.1:3444/WKA2c2STkbrb5LHf' | python3 -c "
import json,sys
cfgs=json.load(sys.stdin)
for c in cfgs:
    for o in c['outbounds']:
        if o['protocol']=='vless':
            ss=o['streamSettings']; sec=ss.get('security')
            fp=(ss.get(sec+'Settings') or {}).get('fingerprint')
            print(c.get('remarks'),'|',o['settings']['vnext'][0]['address'],'|',ss.get('network'),sec,'| fp:',fp,'| sockopt:',ss.get('sockopt'))
    print('   rules:',[r.get('outboundTag') for r in c['routing']['rules']])
"
