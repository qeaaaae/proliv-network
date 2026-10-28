#!/usr/bin/env bash
set -uo pipefail
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
H=(-H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' -H 'X-Forwarded-Proto: https' -H 'Content-Type: application/json')

python3 - <<'PY' > /tmp/lte_patch.json
import json
print(json.dumps({
 "uuid":"499f8118-d8a0-49f2-becf-9627c0069fb8",
 "path":"/api/xhttp",
 "inbound":{"configProfileUuid":"00000000-0000-0000-0000-000000000000","configProfileInboundUuid":"2c993132-0ecf-4a7d-9692-5259aa325d5e"}
}))
PY
curl -s -X PATCH "${H[@]}" --data @/tmp/lte_patch.json "$API/hosts" | python3 -c "import json,sys;d=json.load(sys.stdin);r=d.get('response',d);print(r.get('remark'),'| path:',r.get('path'),'| inbound:',r.get('inbound'))"
