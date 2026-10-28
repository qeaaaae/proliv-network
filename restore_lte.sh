#!/usr/bin/env bash
set -uo pipefail
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
H=(-H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' -H 'X-Forwarded-Proto: https' -H 'Content-Type: application/json')

# restore LTE host to original: VLESS-WS-CDN inbound, path /api/ws
python3 - <<'PY' > /tmp/lte_restore.json
import json
print(json.dumps({
 "uuid":"499f8118-d8a0-49f2-becf-9627c0069fb8",
 "path":"/api/ws",
 "inbound":{"configProfileUuid":"00000000-0000-0000-0000-000000000000","configProfileInboundUuid":"d7b7bf74-239a-45d4-bfdc-b025eb1fa0b6"}
}))
PY
curl -s -X PATCH "${H[@]}" --data @/tmp/lte_restore.json "$API/hosts" | python3 -c "import json,sys;d=json.load(sys.stdin);r=d.get('response',d);print(r.get('remark'),'| path:',r.get('path'),'| inbound bound:',bool((r.get('inbound') or {}).get('configProfileInboundUuid')))"

# show current sub links count
sleep 2
python3 - <<'PY'
import urllib.parse, base64, urllib.request
req=urllib.request.Request('http://127.0.0.1:3444/WKA2c2STkbrb5LHf', headers={'Authorization':'Bearer x'})
raw=urllib.request.urlopen(req,timeout=15).read().decode()
links=[l for l in base64.b64decode(raw).decode().splitlines() if l.startswith('vless://')]
print('links:',len(links))
for l in links:
    u=urllib.parse.urlparse(l)
    print(' ',u.hostname,u.port,urllib.parse.parse_qs(u.query).get('type'),'#',urllib.parse.unquote(l.split('#')[-1]))
PY
