#!/usr/bin/env bash
set -u
URL="https://sub.proliv-network.xyz/WKA2c2STkbrb5LHf"
for UA in "Happ/1.9.2" "happ-proxy/1.0" "Incy/3.8.8" "v2rayNG/1.8.5" "Streisand/1.0" "Mozilla/5.0"; do
  echo "===== UA: $UA ====="
  curl -s --max-time 15 -H "User-Agent: $UA" "$URL" -o /tmp/sub_resp.txt
  CT=$(head -c 60 /tmp/sub_resp.txt | tr -d '\n')
  echo "first bytes: $CT"
  echo "size: $(wc -c < /tmp/sub_resp.txt)"
  grep -oE 'geosite|geolocation|routing' /tmp/sub_resp.txt | sort | uniq -c | head
done
