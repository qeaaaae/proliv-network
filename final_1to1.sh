#!/usr/bin/env bash
set -uo pipefail
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
H=(-H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' -H 'Content-Type: application/json')

echo '=== EE full activeInbounds ==='
curl -s "${H[@]}" "$API/nodes/c0ad1fb9-a8f0-469d-aafb-a3be7763d45f" | python3 -c "
import json,sys
n=json.load(sys.stdin)['response']
for i in n['configProfile']['activeInbounds']:
    print(i['tag'], i['uuid'])
"

echo '=== strip sockoptParams from hosts ==='
for hu in 94a4ca12-7b38-4f87-9cdb-eea87a77511a f5738299-a0d1-429d-9cad-3e3d261484bc ae459449-f6ed-4c52-bb66-7ca92f84b9fa; do
curl -s "${H[@]}" "$API/hosts/$hu" -o /tmp/h.json
python3 - <<'PY' > /tmp/hp.json
import json
d=json.load(open('/tmp/h.json')); h=d.get('response',d)
h['sockoptParams']=None
print(json.dumps(h,ensure_ascii=False))
PY
curl -s -X PATCH "${H[@]}" --data @/tmp/hp.json "$API/hosts" | python3 -c "import json,sys;d=json.load(sys.stdin);r=d.get('response',d);print(r.get('remark'),'| sockopt:',r.get('sockoptParams'))"
done

echo '=== wsSettings.host back to ee.proliv-network.xyz ==='
curl -s "${H[@]}" "$API/config-profiles/00000000-0000-0000-0000-000000000000" -o /tmp/cp.json
python3 - <<'PY' > /tmp/cpp.json
import json
d=json.load(open('/tmp/cp.json')); p=d.get('response',d)
for i in p.get('inbounds',[]):
    if i.get('tag')=='VLESS-WS-CDN':
        i.setdefault('wsSettings',{})['host']='ee.proliv-network.xyz'
        i.setdefault('wsSettings',{})['path']='/api/ws'
body={k:v for k,v in p.items() if k not in ('uuid','createdAt','updatedAt')}
print(json.dumps(body,ensure_ascii=False))
PY
curl -s -X PATCH "${H[@]}" --data @/tmp/cpp.json "$API/config-profiles/00000000-0000-0000-0000-000000000000" | python3 -c "import json,sys;d=json.load(sys.stdin);r=d.get('response',d);[print(i['tag'],i.get('wsSettings')) for i in r.get('inbounds',[])]"
