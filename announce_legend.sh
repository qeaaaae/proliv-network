#!/usr/bin/env bash
set -uo pipefail
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
H=(-H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' -H 'X-Forwarded-Proto: https' -H 'Content-Type: application/json')

echo '=== DE remark ==='
curl -s -X PATCH "${H[@]}" --data '{"uuid":"94a4ca12-7b38-4f87-9cdb-eea87a77511a","remark":"⚡ 🇩🇪 Германия"}' "$API/hosts" | python3 -c "import json,sys;print(json.load(sys.stdin)['response']['remark'])"

echo '=== announce ==='
curl -s "${H[@]}" "$API/subscription-settings" -o /tmp/ss5.json
python3 - <<'PY' > /tmp/ss5p.json
import json
r=json.load(open('/tmp/ss5.json'))['response']
r['customResponseHeaders']['announce']='rwEncodeBase64:🔔 Подписка: {{TELEGRAM_ID}}\n\n⚡ - Нет рекламы на YouTube\n📱 LTE - строго только для мобильного интернета'
body={k:v for k,v in r.items() if k in ('uuid','serveJsonAtBaseSubscription','isShowCustomRemarks','customRemarks','customResponseHeaders','randomizeHosts','responseRules')}
print(json.dumps(body,ensure_ascii=False))
PY
curl -s -X PATCH "${H[@]}" --data @/tmp/ss5p.json "$API/subscription-settings" -o /dev/null

echo '=== what Happ gets ==='
curl -s -D /tmp/hdr.txt -o /tmp/body.json -A 'Happ/5.8.0/ios/2609081608581' 'http://127.0.0.1:3444/WKA2c2STkbrb5LHf'
python3 - <<'PY'
import base64,json
for line in open('/tmp/hdr.txt',encoding='utf-8',errors='replace'):
    if line.lower().startswith('announce:'):
        v=line.split(':',1)[1].strip()
        if v.startswith('base64:'): v=base64.b64decode(v[7:]).decode()
        print('ANNOUNCE >>>'); print(v); print('<<<')
print([c.get('remarks') for c in json.load(open('/tmp/body.json'))])
PY
