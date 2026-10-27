#!/bin/bash
# E2E via teddysun/xray docker (host net): socks -> VLESS/WS/TLS -> EE node.
set -e
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

docker rm -f xray-e2e 2>/dev/null || true
docker run -d --name xray-e2e --network host -v /tmp/ws_client.json:/etc/xray/config.json:ro teddysun/xray:latest xray run -c /etc/xray/config.json
sleep 4
echo "== socks test =="
OUT=$(curl -s --socks5 127.0.0.1:10808 --max-time 15 http://ifconfig.co 2>/dev/null || echo FAIL)
echo "exit_ip=$OUT"
docker logs xray-e2e 2>&1 | tail -6
docker rm -f xray-e2e >/dev/null 2>&1 || true
