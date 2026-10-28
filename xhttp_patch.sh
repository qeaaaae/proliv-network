#!/usr/bin/env bash
set -uo pipefail
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
H=(-H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' -H 'X-Forwarded-Proto: https' -H 'Content-Type: application/json')

# 1. PATCH config profile: add VLESS-XHTTP-CDN inbound on 127.0.0.1:9444
python3 - <<'PY' > /tmp/cp_patch.json
import json
d=json.load(open('/tmp/cp_full.json'))
r=d.get('response',d)
cfg=r['config']
ib={
 "tag":"VLESS-XHTTP-CDN","port":9444,"listen":"127.0.0.1","protocol":"vless",
 "settings":{"clients":[],"decryption":"none"},
 "sniffing":{"enabled":True,"routeOnly":True,"destOverride":["http","tls","quic"]},
 "streamSettings":{"network":"xhttp","security":"none","xhttpSettings":{"path":"/api/xhttp","mode":"auto"}}
}
tags=[i['tag'] for i in cfg['inbounds']]
if 'VLESS-XHTTP-CDN' not in tags:
    cfg['inbounds'].append(ib)
body={"uuid":r['uuid'],"name":r['name'],"config":cfg}
print(json.dumps(body))
PY
curl -s -X PATCH "${H[@]}" --data @/tmp/cp_patch.json "$API/config-profiles" -o /tmp/cp_resp.json
python3 -c "import json;d=json.load(open('/tmp/cp_resp.json'));r=d.get('response',d);ibs=r.get('inbounds',[]);print('inbounds:',[ (i.get('tag'),i.get('uuid')) for i in ibs])"
