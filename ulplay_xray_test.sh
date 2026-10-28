#!/usr/bin/env bash
set -uo pipefail
# download xray to main, push to ulplay
cd /tmp
if [ ! -f /tmp/xray ]; then
  curl -sL -o xray.zip https://github.com/XTLS/Xray-core/releases/download/v26.10.21/Xray-linux-64.zip
  unzip -o -q xray.zip xray geoip.dat geosite.dat -d /tmp/xray-bin 2>/dev/null || unzip -o -q xray.zip -d /tmp/xray-bin
fi
ls -la /tmp/xray-bin/ | head -5
