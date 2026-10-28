#!/usr/bin/env bash
set -uo pipefail
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
H=(-H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' -H 'Content-Type: application/json')

curl -s "${H[@]}" -X POST "$API/hosts" --data '{
 "remark": "⚡ TEST-IP Германия",
 "address": "13.143.192.49",
 "port": 443,
 "sni": "de.proliv-network.xyz",
 "host": "de.proliv-network.xyz",
 "securityLayer": "DEFAULT",
 "fingerprint": "safari",
 "inbound": {"configProfileUuid": "00000000-0000-0000-0000-000000000000", "configProfileInboundUuid": "010eeb5a-4c4d-4bbe-9bec-390ab735b363"}
}' | python3 -c "import json,sys;d=json.load(sys.stdin);r=d.get('response',d);print(r.get('remark'),'|',r.get('address'),'| uuid:',r.get('uuid'))"
