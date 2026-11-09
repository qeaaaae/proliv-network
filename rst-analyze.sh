#!/bin/bash
cd /var/log/xray
echo "=== client IPs by inbound reset count (today) ==="
grep -oE 'readfrom tcp [0-9.]+:443->[0-9.]+:[0-9]+: splice: connection reset by peer' current | grep -oE '>[0-9.]+:' | tr -d '>:' | sort | uniq -c | sort -rn | head -15
echo
echo "=== read: connection reset by peer on inbound side ==="
grep -oE 'read tcp [0-9.]+->[0-9.]+: read: connection reset by peer' current | grep -oE '->[0-9.]+:' | tr -d '->:' | sort | uniq -c | sort -rn | head -15
echo
echo "=== all inbound conn ends, split EOF vs reset ==="
grep -oE 'app/proxyman/inbound: connection ends > [a-zA-Z: ]+' current | sort | uniq -c | sort -rn | head -10
echo
echo "=== top client IPs by REALITY accept (rough) ==="
grep -oE 'from [0-9.]+:[0-9]+ accepted' current | sort | uniq -c | sort -rn | head -5
