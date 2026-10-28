#!/usr/bin/env bash
set -uo pipefail
python3 - <<'PY'
import json, urllib.parse, base64, urllib.request
req=urllib.request.Request('http://127.0.0.1:3444/WKA2c2STkbrb5LHf', headers={'Authorization':'Bearer x'})
raw=urllib.request.urlopen(req,timeout=15).read().decode()
links=[l for l in base64.b64decode(raw).decode().splitlines() if l.startswith('vless://')]
# find the LTE host = ee.proliv-network.xyz port 443 (xhttp or ws whatever type is there)
for l in links:
    u=urllib.parse.urlparse(l)
    if u.hostname=='ee.proliv-network.xyz':
        print('FOUND ee link:', l[:120])
        q=urllib.parse.parse_qs(u.query)
        print('type',q.get('type'),'path',q.get('path'),'mode',q.get('mode'))
PY
