#!/usr/bin/env bash
cd /opt/app
R=node_modules/@remnawave/backend-contract/build/backend/api/routes.js
grep -oE "'[^']*'" $R | grep -iE 'template|subscr' | sort -u | head -30
echo "=== controllers in dist ==="
grep -oE '@(Get|Post|Patch|Delete|Put)\([^)]*\)' dist/app.js 2>/dev/null | head -40
echo "=== try paths ==="
for p in subscription-templates subscription-template templates/xray-json xray-json-templates; do
  echo "--- $p"
done
