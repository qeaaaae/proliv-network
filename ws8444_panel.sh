#!/usr/bin/env bash
set -uo pipefail
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
H=(-H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' -H 'X-Forwarded-Proto: https' -H 'Content-Type: application/json')
WSIB="d7b7bf74-239a-45d4-bfdc-b025eb1fa0b6"
REIB="010eeb5a-4c4d-4bbe-9bec-390ab735b363"
DE="b4393e6a-7369-4b93-8dd9-4c5381554544"
UK="cefc979e-22dd-40e6-81ee-55141feb01b6"
EE="c0ad1fb9-a8f0-469d-aafb-a3be7763d45f"
PROF="00000000-0000-0000-0000-000000000000"

# 1. enable WS inbound on DE + UK (EE already has it)
for nid in $DE $UK; do
  python3 - <<PY > /tmp/np.json
import json
print(json.dumps({"uuid":"$nid","configProfile":{"activeConfigProfileUuid":"$PROF","activeInbounds":["$REIB","$WSIB"]}}))
PY
  curl -s -X PATCH "${H[@]}" --data @/tmp/np.json "$API/nodes" | python3 -c "import json,sys;d=json.load(sys.stdin);r=d.get('response',d);print(r.get('name'),'->',[i['tag'] for i in r.get('configProfile',{}).get('activeInbounds',[])])"
done

# 2. create 3 ws-8444 hosts
python3 - <<'PY' > /tmp/hosts_mk.jsonl
import json
mk=[
 ("🇩🇪 Германия резерв","de.proliv-network.xyz","b4393e6a-7369-4b93-8dd9-4c5381554544"),
 ("🇬🇧 Великобритания резерв","uk.proliv-network.xyz","cefc979e-22dd-40e6-81ee-55141feb01b6"),
 ("🇪🇪 Эстония резерв","ee-src.proliv-network.xyz","c0ad1fb9-a8f0-469d-aafb-a3be7763d45f"),
]
for remark,addr,nid in mk:
    print(json.dumps({"remark":remark,"address":addr,"port":8444,"path":"/api/ws","sni":addr,"host":addr,
      "fingerprint":"safari","securityLayer":"TLS",
      "inbound":{"configProfileUuid":"00000000-0000-0000-0000-000000000000","configProfileInboundUuid":"d7b7bf74-239a-45d4-bfdc-b025eb1fa0b6"},
      "nodes":[nid]}), flush=True)
PY
while read -r body; do
  echo "$body" > /tmp/mkh.json
  curl -s -X POST "${H[@]}" --data @/tmp/mkh.json "$API/hosts" | python3 -c "import json,sys;d=json.load(sys.stdin);r=d.get('response',d);print('created:',r.get('remark'),r.get('uuid'))" 2>/dev/null || cat /tmp/mkh.json
done < /tmp/hosts_mk.jsonl
