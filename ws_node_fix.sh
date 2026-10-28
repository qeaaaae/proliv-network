#!/usr/bin/env bash
set -uo pipefail
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
H=(-H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' -H 'Content-Type: application/json')

curl -s "${H[@]}" "$API/nodes/b4393e6a-7369-4b93-8dd9-4c5381554544" | python3 -c "import json,sys;n=json.load(sys.stdin)['response'];print(list(n.keys()));print(json.dumps(n.get('configProfile'),ensure_ascii=False))"
