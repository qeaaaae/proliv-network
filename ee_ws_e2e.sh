#!/bin/bash
# E2E: xray client -> VLESS/WS/TLS to ee.proliv-network.xyz:443 -> EE node exit.
set -e
XRAY=/usr/local/bin/xray
[ -x "$XRAY" ] || XRAY=/root/xray
[ -x "$XRAY" ] || XRAY=$(which xray || true)
echo "xray: $XRAY"

cat > /tmp/ws_client.json <<'EOF'
{
  "log": {"loglevel": "warning"},
  "inbounds": [{
    "tag": "socks-in",
    "port": 10808,
    "listen": "127.0.0.1",
    "protocol": "socks",
    "settings": {"auth": "noauth", "udp": true}
  }],
  "outbounds": [{
    "tag": "proxy",
    "protocol": "vless",
    "settings": {
      "vnext": [{
        "address": "ee.proliv-network.xyz",
        "port": 443,
        "users": [{"id": "0a7264c4-3494-43db-b1fa-f50545f974e3", "encryption": "none"}]
      }]
    },
    "streamSettings": {
      "network": "ws",
      "security": "tls",
      "tlsSettings": {"serverName": "ee.proliv-network.xyz", "fingerprint": "safari"},
      "wsSettings": {"path": "/api/ws", "headers": {"Host": "ee.proliv-network.xyz"}}
    }
  }]
}
EOF

$XRAY run -c /tmp/ws_client.json > /tmp/ws_xray.log 2>&1 &
XPID=$!
sleep 3
echo "== socks test =="
OUT=$(curl -s --socks5 127.0.0.1:10808 --max-time 15 http://ifconfig.co 2>/dev/null || echo FAIL)
echo "exit_ip=$OUT"
kill $XPID 2>/dev/null
tail -5 /tmp/ws_xray.log
