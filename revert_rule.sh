#!/usr/bin/env bash
set -euo pipefail
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
H=(-H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' -H 'X-Forwarded-Proto: https')

curl -s "${H[@]}" "$API/subscription-settings" -o /tmp/subset.json
python3 - <<'PY'
import json
d=json.load(open('/tmp/subset.json'))
r=d.get('response',d) if isinstance(d,dict) else d
rr=r.get('responseRules',{})
rr['rules']=[x for x in rr['rules'] if x.get('name')!='Happ/Incy Xray JSON']
body={
  "uuid": r.get('uuid'),
  "serveJsonAtBaseSubscription": r.get('serveJsonAtBaseSubscription'),
  "isShowCustomRemarks": r.get('isShowCustomRemarks'),
  "customRemarks": r.get('customRemarks'),
  "customResponseHeaders": r.get('customResponseHeaders'),
  "randomizeHosts": r.get('randomizeHosts'),
  "responseRules": rr,
}
open('/tmp/ss_revert.json','w').write(json.dumps(body,ensure_ascii=False))
print('rules now:', [x['name'] for x in rr['rules']])
PY
curl -s -X PATCH "${H[@]}" -H 'Content-Type: application/json' --data-binary @/tmp/ss_revert.json "$API/subscription-settings" -o /dev/null

echo "=== verify: incy gets base64 again ==="
curl -s --max-time 15 -H "User-Agent: INCY/3.8.8" "https://sub.proliv-network.xyz/WKA2c2STkbrb5LHf" | head -c 60; echo

echo "=== check template content (default xray json) ==="
curl -s "${H[@]}" "$API/subscription-templates" -o /tmp/tpls.json
python3 - <<'PY'
import json
d=json.load(open('/tmp/tpls.json'))
r=d.get('response',d) if isinstance(d,dict) else d
for t in r.get('templates',[]):
    print(t.get('uuid'),'|',t.get('name'),'|',t.get('templateType'),'| json?', t.get('templateJson') is not None, '| yaml?', t.get('encodedTemplateYaml') is not None)
PY
