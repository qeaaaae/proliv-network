#!/usr/bin/env bash
cd ~
./bin/xray run -c ru_client.json > /tmp/xray_cl.log 2>&1 &
echo $! > /tmp/xray_cl.pid
sleep 5
echo "=== client log ==="
cat /tmp/xray_cl.log | tail -15
echo "=== socks test ==="
for i in 1 2 3; do
  curl -s --max-time 15 --socks5-hostname 127.0.0.1:10901 https://ifconfig.co/json 2>/dev/null && break
  echo "attempt $i failed"; sleep 2
done
kill $(cat /tmp/xray_cl.pid) 2>/dev/null
