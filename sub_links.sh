#!/bin/bash
# Decode raw subscription and show generated vless links.
curl -sk "https://sub.proliv-network.xyz/-_9jFSnmwY9NBaCP" -H "User-Agent: v2rayN/7.0" -o /tmp/sub_raw.txt
base64 -d /tmp/sub_raw.txt 2>/dev/null | grep -E "^vless://" | sed 's/#[^#]*$//' | head -10
echo "=== also check headers ==="
head -5 /tmp/sub_raw.txt | cut -c1-80
