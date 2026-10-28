#!/usr/bin/env bash
set -uo pipefail
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
H=(-H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' -H 'X-Forwarded-Proto: https' -H 'Content-Type: application/json')
for uuid in d406e85b-294c-4316-af39-5baacd87cb66 0166a459-a6f9-400e-b8f7-bc35fb028e4e 62027def-6ac5-4d41-8a20-6ad3aa380227; do
  python3 -c "import json;print(json.dumps({'uuid':'$uuid','port':443}))" > /tmp/hp2.json
  curl -s -X PATCH "${H[@]}" --data @/tmp/hp2.json "$API/hosts" | python3 -c "import json,sys;d=json.load(sys.stdin);r=d.get('response',d);print(r.get('remark'),'->',r.get('port'))"
done
echo "=== new links ==="
sleep 2
python3 - <<'PY'
import urllib.parse, base64, urllib.request
req=urllib.request.Request('http://127.0.0.1:3444/WKA2c2STkbrb5LHf', headers={'Authorization':'Bearer x'})
raw=urllib.request.urlopen(req,timeout=15).read().decode()
for l in base64.b64decode(raw).decode().splitlines():
    if l.startswith('vless://'):
        u=urllib.parse.urlparse(l); q=urllib.parse.parse_qs(u.query)
        if u.port==443 and q.get('type',[''])[0]=='ws':
            print(l)
PY
