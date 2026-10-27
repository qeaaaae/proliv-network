#!/bin/bash
# EE via Yandex CDN: add VLESS-WS inbound to Default-Profile, activate on EE node,
# enable in squad, create CDN host, repoint EE Reality host to ee-src.
set -u
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
EE_NODE="c0ad1fb9-a8f0-469d-aafb-a3be7763d45f"
SQUAD="2b5f5dcd-0099-4f51-bc26-0ba04c240d63"
EE_HOST="ae459449-f6ed-4c52-bb66-7ca92f84b9fa"
PROFILE="00000000-0000-0000-0000-000000000000"
REALITY_INBOUND="010eeb5a-4c4d-4bbe-9bec-390ab735b363"

req() { # method path body
  curl -s -X "$1" -H "Authorization: Bearer $JWT" -H "Content-Type: application/json" \
    ${3:+-d "$3"} "$API$2"
}

echo "== 1. fetch current profile, append WS inbound =="
req GET "/config-profiles/$PROFILE" > /tmp/prof_before.json
python3 - <<'PY'
import json
d = json.load(open('/tmp/prof_before.json'))
cfg = d['response']['config']
inbs = cfg['inbounds']
if any(i.get('tag') == 'VLESS-WS-CDN' for i in inbs):
    print('WS inbound already present')
else:
    inbs.append({
        "tag": "VLESS-WS-CDN",
        "port": 9443,
        "listen": "127.0.0.1",
        "protocol": "vless",
        "settings": {"clients": [], "decryption": "none"},
        "sniffing": {"enabled": True, "routeOnly": True, "destOverride": ["http", "tls", "quic"]},
        "streamSettings": {
            "network": "ws",
            "security": "none",
            "wsSettings": {"path": "/api/ws", "host": "ee.proliv-network.xyz"}
        }
    })
json.dump({"uuid": "00000000-0000-0000-0000-000000000000", "config": cfg}, open('/tmp/prof_patch.json', 'w'))
print('inbounds:', [i.get('tag') for i in inbs])
PY

echo "== 2. PATCH profile (try PATCH then POST) =="
resp=$(req PATCH "/config-profiles/" "$(cat /tmp/prof_patch.json)")
echo "$resp" | head -c 300; echo
if echo "$resp" | grep -q '"response"'; then :; else
  resp=$(req POST "/config-profiles/" "$(cat /tmp/prof_patch.json)")
  echo "$resp" | head -c 300; echo
fi
echo "$resp" > /tmp/prof_after.json
WS_INBOUND=$(python3 -c "import json;d=json.load(open('/tmp/prof_after.json'));print([i['uuid'] for i in d['response']['inbounds'] if i['tag']=='VLESS-WS-CDN'][0])")
echo "WS_INBOUND=$WS_INBOUND"

echo "== 3. activate both inbounds on EE node =="
resp=$(req PATCH "/nodes/" "{\"uuid\":\"$EE_NODE\",\"configProfile\":{\"activeConfigProfileUuid\":\"$PROFILE\",\"activeInbounds\":[\"$REALITY_INBOUND\",\"$WS_INBOUND\"]}}")
echo "$resp" | python3 -c "import json,sys;d=json.load(sys.stdin);n=d.get('response',d);print('node:',n.get('name'),'inbounds:',[i['tag'] for i in n.get('configProfile',{}).get('activeInbounds',[])])" 2>/dev/null || echo "$resp" | head -c 400

echo "== 4. enable inbounds in Default-Squad =="
resp=$(req PATCH "/internal-squads/" "{\"uuid\":\"$SQUAD\",\"inbounds\":[\"$REALITY_INBOUND\",\"$WS_INBOUND\"]}")
echo "$resp" | python3 -c "import json,sys;d=json.load(sys.stdin);print('squad inbounds:',[i['tag'] for i in d.get('response',{}).get('inbounds',[])])" 2>/dev/null || echo "$resp" | head -c 400

echo "== 5. create WS CDN host =="
resp=$(req POST "/hosts/" "{\"inbound\":{\"configProfileUuid\":\"$PROFILE\",\"configProfileInboundUuid\":\"$WS_INBOUND\"},\"remark\":\"EE CDN\",\"address\":\"ee.proliv-network.xyz\",\"port\":443,\"path\":\"/api/ws\",\"sni\":\"ee.proliv-network.xyz\",\"host\":\"ee.proliv-network.xyz\",\"fingerprint\":\"safari\",\"securityLayer\":\"TLS\",\"nodes\":[\"$EE_NODE\"]}")
echo "$resp" | head -c 500; echo

echo "== 6. repoint EE Reality host address -> ee-src =="
resp=$(req PATCH "/hosts/" "{\"uuid\":\"$EE_HOST\",\"address\":\"ee-src.proliv-network.xyz\",\"sni\":\"ee.proliv-network.xyz\"}")
echo "$resp" | python3 -c "import json,sys;d=json.load(sys.stdin);h=d.get('response',d);print('host:',h.get('remark'),'addr:',h.get('address'),'sni:',h.get('sni'))" 2>/dev/null || echo "$resp" | head -c 400

echo "== 7. verify hosts =="
req GET "/hosts" | python3 -c "import json,sys;d=json.load(sys.stdin);[print(h.get('remark'),'|',h.get('address'),'| sni:',h.get('sni'),'| path:',h.get('path')) for h in d.get('response',[])]"
