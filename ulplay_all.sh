#!/usr/bin/env bash
set -uo pipefail
cd ~
for name in de uk ee-src ee; do
  echo "===== $name ====="
  ./bin/xray run -c ru_$name.json > /tmp/xl_$name.log 2>&1 &
  pid=$!
  sleep 4
  for i in 1 2; do
    out=$(curl -s --max-time 15 --socks5-hostname 127.0.0.1:10901 https://ifconfig.co/json 2>/dev/null)
    [ -n "$out" ] && break
    sleep 2
  done
  if [ -n "$out" ]; then echo "OK: $out"; else echo "FAIL"; tail -6 /tmp/xl_$name.log; fi
  kill $pid 2>/dev/null
done
