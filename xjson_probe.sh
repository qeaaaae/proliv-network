#!/usr/bin/env bash
set -uo pipefail
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
H=(-H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' -H 'X-Forwarded-Proto: https')

echo "=== xray-json template ==="
curl -s "${H[@]}" "$API/xray-json-template" -o /tmp/tpl.json
python3 -c "
import json
d=json.load(open('/tmp/tpl.json'))
r=d.get('response',d)
print(type(r), list(r.keys()) if isinstance(r,dict) else len(r))
s=json.dumps(r,ensure_ascii=False)
print('len',len(s))
import re
for m in re.finditer(r'geolocation-ru|category-ru|geoip|geosite|fragment|fingerprint', s):
    a=max(0,m.start()-80); print('...',s[a:m.end()+80],'...')
"
