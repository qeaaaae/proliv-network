#!/usr/bin/env bash
set -u
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
H=(-H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' -H 'X-Forwarded-Proto: https')

echo "=== subscription-settings ==="
curl -s "${H[@]}" "$API/subscription-settings" -o /tmp/subset.json
python3 - <<'PY'
import json
d=json.load(open('/tmp/subset.json'))
r=d.get('response',d) if isinstance(d,dict) else d
print(json.dumps(r,ensure_ascii=False,indent=1)[:2500])
PY

echo
echo "=== response-rules endpoint probe ==="
for p in "/subscription-settings/response-rules" "/response-rules" "/subscription-response-rules"; do
  code=$(curl -s -o /tmp/rr.json -w '%{http_code}' "${H[@]}" "$API$p")
  echo "$p -> $code $(head -c 120 /tmp/rr.json)"
done
