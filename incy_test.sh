#!/usr/bin/env bash
set -euo pipefail
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
H=(-H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' -H 'X-Forwarded-Proto: https')

# add XRAY_JSON rule for incy/happ UAs at the FRONT of rules list (before browser)
python3 - <<'PY'
import json
d=json.load(open('/tmp/subset.json'))
r=d.get('response',d) if isinstance(d,dict) else d
rr=r.get('responseRules',{})
new_rule = {
  "name": "Happ/Incy Xray JSON",
  "enabled": True,
  "operator": "OR",
  "conditions": [
    {"value": "^(happ|incy)", "operator": "REGEX", "headerName": "user-agent", "caseSensitive": False}
  ],
  "description": "Full xray JSON config so client-side routing presets are not applied",
  "responseType": "XRAY_JSON"
}
rr['rules'] = [new_rule] + rr['rules']
body = {
  "uuid": r.get('uuid'),
  "serveJsonAtBaseSubscription": r.get('serveJsonAtBaseSubscription'),
  "isShowCustomRemarks": r.get('isShowCustomRemarks'),
  "customRemarks": r.get('customRemarks'),
  "customResponseHeaders": r.get('customResponseHeaders'),
  "randomizeHosts": r.get('randomizeHosts'),
  "responseRules": rr,
}
open('/tmp/ss_patch2.json','w').write(json.dumps(body, ensure_ascii=False))
print('rules count:', len(rr['rules']))
PY

curl -s -X PATCH "${H[@]}" -H 'Content-Type: application/json' --data-binary @/tmp/ss_patch2.json "$API/subscription-settings" -o /dev/null

echo "=== fetch as Incy ==="
curl -s --max-time 15 -H "User-Agent: INCY/3.8.8" "https://sub.proliv-network.xyz/WKA2c2STkbrb5LHf" -o /tmp/incy_resp.txt
echo "size: $(wc -c < /tmp/incy_resp.txt)"
head -c 200 /tmp/incy_resp.txt; echo
echo "=== routing section in xray json ==="
python3 - <<'PY'
import json
try:
    d=json.load(open('/tmp/incy_resp.txt'))
    print('keys:', list(d.keys()))
    rt=d.get('routing',{})
    print('routing:', json.dumps(rt,ensure_ascii=False)[:800])
    obs=d.get('outbounds',[])
    print('outbounds:', len(obs))
except Exception as e:
    print('not json:', e)
    print(open('/tmp/incy_resp.txt').read()[:300])
PY
