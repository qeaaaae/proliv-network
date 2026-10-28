#!/usr/bin/env bash
cd ~
./bin/xray run -c cfg_de.json > /tmp/cfg_de.log 2>&1 &
pid=$!
sleep 4
cat /tmp/cfg_de.log | tail -8
for i in 1 2; do
  out=$(curl -s --max-time 15 --socks5-hostname 127.0.0.1:10902 https://ifconfig.co/json 2>/dev/null | python3 -c 'import json,sys;print(json.load(sys.stdin)["ip"])' 2>/dev/null)
  [ -n "$out" ] && break
  sleep 2
done
[ -n "$out" ] && echo "DE via JSON config: OK exit=$out" || { echo FAIL; tail -5 /tmp/cfg_de.log; }
kill $pid 2>/dev/null
