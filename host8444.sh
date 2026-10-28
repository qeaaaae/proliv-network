#!/usr/bin/env bash
set -uo pipefail
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
H=(-H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' -H 'Content-Type: application/json')
curl -s "${H[@]}" -X POST "$API/hosts" --data '{
 "remark": "🇩🇪 Германия 2",
 "address": "de.proliv-network.xyz",
 "port": 8444,
 "path": "/api/ws",
 "host": "de.proliv-network.xyz",
 "sni": "de.proliv-network.xyz",
 "securityLayer": "TLS",
 "fingerprint": "safari",
 "inbound": {"configProfileUuid": "00000000-0000-0000-0000-000000000000", "configProfileInboundUuid": "d7b7bf74-239a-45d4-bfdc-b025eb1fa0b6"}
}' | python3 -c "import json,sys;d=json.load(sys.stdin);r=d.get('response',d);print(r.get('remark'),'|',r.get('address'),r.get('port'),r.get('path'))"
