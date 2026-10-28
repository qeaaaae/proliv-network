#!/usr/bin/env bash
set -uo pipefail
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
H=(-H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' -H 'X-Forwarded-Proto: https')
curl -s "${H[@]}" "$API/subscription-templates" -o /tmp/templates.json
python3 - <<'PY'
import json
d=json.load(open('/tmp/templates.json'))
r=d.get('response',d)
items=r if isinstance(r,list) else r.get('items',r.get('templates',[]))
for t in items:
    print('---',t.get('uuid'),'|',t.get('name'),'| type:',t.get('templateType'),'| isDefault:',t.get('isDefault'))
    c=json.dumps(t.get('templateJson') or t.get('encodedTemplateYaml') or '',ensure_ascii=False)
    print('  len',len(c))
PY
