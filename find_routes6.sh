#!/usr/bin/env bash
cd /opt/app
R=dist/node_modules/@remnawave/backend-contract/build/backend/api/routes.js
[ -f "$R" ] || R=$(find . -name routes.js -path '*backend-contract*' | head -1)
echo "ROUTES FILE: $R"
grep -oE "'[^']*'" "$R" | grep -iE 'template|subscr|xray' | sort -u | head -40
