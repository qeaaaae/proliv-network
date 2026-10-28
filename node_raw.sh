#!/usr/bin/env bash
set -uo pipefail
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
curl -s -H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' 'http://127.0.0.1:3443/api/nodes' | python3 -c "
import json,sys
d=json.load(sys.stdin)
for n in d['response']:
    print(n['name'], n.get('uuid'))
    for k,v in n.items():
        if 'bound' in k.lower() or 'inbound' in k.lower():
            print('  ',k,'=',v)
"
