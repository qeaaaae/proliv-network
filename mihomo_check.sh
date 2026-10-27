#!/usr/bin/env bash
set -u
for UA in "mihomo/1.18" "clash-meta/1.0" "sing-box/1.10" "Stash/2.5"; do
  echo "===== $UA ====="
  curl -s --max-time 15 -H "User-Agent: $UA" "https://sub.proliv-network.xyz/WKA2c2STkbrb5LHf" -o /tmp/r.txt
  echo "size: $(wc -c < /tmp/r.txt)"
  grep -oE "geosite:[a-zA-Z!.-]+|GEOLOCATION-[A-Z!]+|category-ru" /tmp/r.txt | sort | uniq -c || echo "(no geosite refs)"
done
