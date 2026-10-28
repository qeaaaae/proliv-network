#!/usr/bin/env bash
cd /opt/app
echo "=== template-related strings ==="
grep -oE '"[a-zA-Z0-9/_-]*[Tt]emplate[a-zA-Z0-9/_-]*"' dist/app.js | sort -u | head -20
grep -oE "xrayJsonTemplate[a-zA-Z]*" dist/app.js | sort -u | head
echo "=== routes containing 'template' ==="
grep -oE "'(GET|POST|PATCH|DELETE|PUT)'[^,]{0,120}" dist/app.js | grep -i template | head -20
echo "=== subscription-settings routes ==="
grep -oE "'(GET|POST|PATCH|DELETE|PUT)'[^,]{0,120}" dist/app.js | grep -iE 'subscription|subpage' | head -30
