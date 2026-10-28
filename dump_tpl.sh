#!/usr/bin/env bash
set -uo pipefail
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
curl -s -H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' -H 'X-Forwarded-Proto: https' \
  http://127.0.0.1:3443/api/subscription-templates/3a575487-4b1d-47da-901e-9e928254385a \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); print(json.dumps(d["response"]["templateJson"],indent=1,ensure_ascii=False))'
