#!/usr/bin/env bash
set -uo pipefail
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
H=(-H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' -H 'Content-Type: application/json')

echo '=== UK inbounds ==='
curl -s "${H[@]}" "$API/nodes/cefc979e-22dd-40e6-81ee-55141feb01b6" | python3 -c "import json,sys;n=json.load(sys.stdin)['response'];[print(i['tag']) for i in n['configProfile']['activeInbounds']]"

echo '=== create ws hosts ==='
mk() {
curl -s "${H[@]}" -X POST "$API/hosts" --data "$1" | python3 -c "import json,sys;d=json.load(sys.stdin);r=d.get('response',d);print(r.get('remark'),'|',r.get('address'),r.get('path'))"
}
mk '{"remark":"🇩🇪 Германия (WS)","address":"de.proliv-network.xyz","port":443,"path":"/api/ws","host":"de.proliv-network.xyz","sni":"de.proliv-network.xyz","securityLayer":"TLS","fingerprint":"safari","inbound":{"configProfileUuid":"00000000-0000-0000-0000-000000000000","configProfileInboundUuid":"d7b7bf74-239a-45d4-bfdc-b025eb1fa0b6"}}'
mk '{"remark":"🇬🇧 Великобритания (WS)","address":"uk.proliv-network.xyz","port":443,"path":"/api/ws","host":"uk.proliv-network.xyz","sni":"uk.proliv-network.xyz","securityLayer":"TLS","fingerprint":"safari","inbound":{"configProfileUuid":"00000000-0000-0000-0000-000000000000","configProfileInboundUuid":"d7b7bf74-239a-45d4-bfdc-b025eb1fa0b6"}}'
mk '{"remark":"🇪🇪 Эстония (WS)","address":"ee-src.proliv-network.xyz","port":443,"path":"/api/ws","host":"ee.proliv-network.xyz","sni":"ee.proliv-network.xyz","securityLayer":"TLS","fingerprint":"safari","inbound":{"configProfileUuid":"00000000-0000-0000-0000-000000000000","configProfileInboundUuid":"d7b7bf74-239a-45d4-bfdc-b025eb1fa0b6"}}'
