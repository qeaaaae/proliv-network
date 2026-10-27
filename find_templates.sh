#!/usr/bin/env bash
set -u
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
H=(-H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' -H 'X-Forwarded-Proto: https')

for p in "/subscription-templates" "/subscription-template" "/templates" "/subscription/templates"; do
  code=$(curl -s -o /tmp/tpl.json -w '%{http_code}' "${H[@]}" "$API$p")
  echo "$p -> $code"
  [ "$code" = "200" ] && head -c 300 /tmp/tpl.json && echo && break
done

echo "=== where does geolocation-ru come from? check full incy response ==="
python3 - <<'PY'
import json
d=json.load(open('/tmp/incy_resp.txt'))
cfg = d[0] if isinstance(d,list) else d
print(json.dumps(cfg.get('routing'),ensure_ascii=False,indent=1))
print('---outbound tags---')
for o in cfg.get('outbounds',[]):
    print(o.get('tag'), o.get('protocol'))
PY
