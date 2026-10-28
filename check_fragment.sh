#!/usr/bin/env bash
cd /tmp/xray-bin
grep -aoE 'tlshello' xray | head -3
echo '---'
grep -aoE 'fragment' xray | head -3
echo '--- test config with fragment ---'
cat > /tmp/fragtest.json <<'EOF'
{"log":{"loglevel":"debug"},"inbounds":[],"outbounds":[{"tag":"p","protocol":"vless","settings":{"vnext":[{"address":"127.0.0.1","port":443,"users":[{"id":"00000000-0000-0000-0000-000000000000","encryption":"none"}]}]},"streamSettings":{"network":"tcp","security":"reality","realitySettings":{"serverName":"x","publicKey":"x","shortId":"","fingerprint":"safari"},"sockopt":{"fragment":{"packets":"tlshello","length":"50-150","interval":"10-50"}}}}]}
EOF
./xray run -test -c /tmp/fragtest.json 2>&1 | tail -5
