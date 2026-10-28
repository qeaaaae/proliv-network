#!/usr/bin/env bash
set -uo pipefail
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
H=(-H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' -H 'X-Forwarded-Proto: https' -H 'Content-Type: application/json')

# check squad update schema
U=/var/lib/docker/rootfs/overlayfs/9743afaecf0ed3f2d6cf96a7fc4943ca69c10c16f71243224a9072593ea2d4b3/opt/app/dist/node_modules/@remnawave/backend-contract/build/backend/commands/internal-squads/update.command.js
[ -f "$U" ] && grep -oE 'RequestBodySchema[^;]{0,700}' "$U" | head -3

python3 - <<'PY' > /tmp/sq_patch.json
import json
print(json.dumps({"uuid":"2b5f5dcd-0099-4f51-bc26-0ba04c240d63","inbounds":["010eeb5a-4c4d-4bbe-9bec-390ab735b363","d7b7bf74-239a-45d4-bfdc-b025eb1fa0b6","2c993132-0ecf-4a7d-9692-5259aa325d5e"]}))
PY
cat /tmp/sq_patch.json; echo
curl -s -X PATCH "${H[@]}" --data @/tmp/sq_patch.json "$API/internal-squads" | python3 -c "import json,sys;d=json.load(sys.stdin);r=d.get('response',d);print(json.dumps(r,ensure_ascii=False)[:400])"
