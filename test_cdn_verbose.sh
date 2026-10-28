#!/usr/bin/env bash
set -uo pipefail
echo "=== raw link ==="
grep 'ee.proliv-network' /tmp/sub_links.txt || grep 'ee\.' /tmp/sub_links.txt | tail -1
echo
echo "=== ws handshake probe via CDN ==="
curl -s -i --max-time 15 "https://ee.proliv-network.xyz/api/ws" \
  -H "Connection: Upgrade" -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" -H "Sec-WebSocket-Version: 13" | head -8
echo
echo "=== retry xray client on CDN link, verbose ==="
docker rm -f xraytest >/dev/null 2>&1
docker run -d --name xraytest --network host -v /tmp/client_3.json:/etc/xray/config.json teddysun/xray xray run -c /etc/xray/config.json >/dev/null
sleep 5
docker logs xraytest 2>&1 | tail -8
curl -s --max-time 20 --socks5-hostname 127.0.0.1:10900 https://ifconfig.co/json || echo "CURL FAILED"
echo
docker rm -f xraytest >/dev/null 2>&1
