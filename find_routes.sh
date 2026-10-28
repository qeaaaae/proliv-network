#!/usr/bin/env bash
R=/opt/app/node_modules/@remnawave/backend-contract/build/backend/api/routes.js
grep -oE '"/[a-zA-Z0-9/_{}-]+"' $R 2>/dev/null | sort -u | grep -iE 'subscr|xray|template|config' | head -40
echo "=== ALT grep ==="
grep -oE "[a-zA-Z_]+:[ ]*'[^']+'" $R 2>/dev/null | grep -iE 'xray|template|subscr' | sort -u | head -40
