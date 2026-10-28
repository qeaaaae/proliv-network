#!/usr/bin/env bash
set -uo pipefail
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
H=(-H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' -H 'X-Forwarded-Proto: https')
curl -s "${H[@]}" "$API/subscription-settings" | python3 -c "
import json,sys
r=json.load(sys.stdin)['response']
for k,v in r['customResponseHeaders'].items(): print(k,'=',v[:200])
"
echo '=== template keys in panel ==='
docker exec remnawave sh -c "grep -rhoE '\{\{[A-Z_]+\}\}' /opt/app/dist 2>/dev/null | sort | uniq -c | sort -rn | head -40"
echo '=== headers templated? ==='
docker exec remnawave sh -c "grep -rlE 'customResponseHeaders' /opt/app/dist 2>/dev/null | head -5"
