#!/usr/bin/env bash
cd /opt/app
ls dist/modules 2>/dev/null | head -30
echo "=== grep xrayJson in dist ==="
grep -rl "xrayJson\|xray-json\|XRAY_JSON\|subscriptionTemplate" dist/ 2>/dev/null | head -10
echo "=== subscription settings fields ==="
grep -oE '"[a-zA-Z]+":' dist/modules/subscription*/**/*.js 2>/dev/null | sort -u | head -60
