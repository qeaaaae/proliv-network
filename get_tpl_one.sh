#!/usr/bin/env bash
set -uo pipefail
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
H=(-H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' -H 'X-Forwarded-Proto: https')
echo "=== one template ==="
curl -s "${H[@]}" "$API/subscription-templates/3a575487-4b1d-47da-901e-9e928254385a" | python3 -m json.tool | head -40
echo "=== contract: template schema ==="
F=/var/lib/docker/rootfs/overlayfs/9743afaecf0ed3f2d6cf96a7fc4943ca69c10c16f71243224a9072593ea2d4b3/opt/app/dist/node_modules/@remnawave/backend-contract/build/backend
grep -rn "templateJson\|templateType\|XRAY_JSON" $F --include='*.d.ts' -l 2>/dev/null | head -5
