#!/usr/bin/env bash
set -uo pipefail
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
H=(-H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' -H 'X-Forwarded-Proto: https')
curl -s "${H[@]}" "$API/hosts" | python3 -c "
import json,sys
d=json.load(sys.stdin); r=d.get('response',d)
hosts=r.get('hosts',r.get('items')) if isinstance(r,dict) else r
for h in hosts:
    if h.get('uuid')=='499f8118-d8a0-49f2-becf-9627c0069fb8':
        print(json.dumps({k:h.get(k) for k in ('remark','address','port','path','sni','host','isDisabled','securityLayer','xhttpExtraParams','inbound','nodes','internalSquads')},ensure_ascii=False,indent=1))
"
