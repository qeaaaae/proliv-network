#!/usr/bin/env bash
cd /opt/app
echo "=== xrayJson context in app.js ==="
grep -oE ".{80}xrayJson.{80}" dist/app.js | head -10
echo "=== template endpoints ==="
grep -oE "'/[a-zA-Z0-9/_:{}-]+'" dist/app.js | sort -u | grep -iE 'template|json|sub' | head -30
echo "=== subscription controllers ==="
find dist -name '*.js' | xargs grep -l "subscription" 2>/dev/null | head -10
