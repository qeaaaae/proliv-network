#!/usr/bin/env bash
set -uo pipefail
NAMES=("DE-Reality" "UK-Reality" "EE-Reality" "EE-CDN-WS")
for i in 0 1 2 3; do
  echo "===== ${NAMES[$i]} ====="
  docker rm -f xraytest >/dev/null 2>&1
  docker run -d --name xraytest --network host -v /tmp/client_$i.json:/etc/xray/config.json teddysun/xray xray run -c /etc/xray/config.json >/dev/null
  sleep 4
  docker logs xraytest 2>&1 | tail -3
  curl -s --max-time 15 --socks5-hostname 127.0.0.1:10900 https://ifconfig.co/json 2>/dev/null | python3 -c "import sys,json;d=json.load(sys.stdin);print('EXIT IP:',d.get('ip'),'|',d.get('country'),'|',d.get('org',''))" || echo "FAILED (no traffic through)"
  docker rm -f xraytest >/dev/null 2>&1
  echo
done
