#!/bin/bash
cd /var/log/nginx
echo "=== session lifespans (top 15 by requests) ==="
for s in $(grep -oE 'sess_id=[a-f0-9-]+' access.log | sort | uniq -c | sort -rn | head -15 | awk '{print $2}'); do
    first=$(grep "$s" access.log | head -1 | grep -oE '[0-9]{2}:[0-9]{2}:[0-9]{2}' | head -1)
    last=$(grep "$s" access.log | tail -1 | grep -oE '[0-9]{2}:[0-9]{2}:[0-9]{2}' | tail -1)
    reqs=$(grep -c "$s" access.log)
    maxseg=$(grep "$s" access.log | grep -oE 'segment=[0-9]+' | cut -d= -f2 | sort -n | tail -1)
    ip=$(grep "$s" access.log | head -1 | awk '{print $1}')
    echo "$s reqs=$reqs span=$first-$last maxseg=$maxseg ip=$ip"
done
echo
echo "=== NEW sess_id appearances per minute (first-seen time) ==="
grep 'sess_id' access.log | grep -oE 'sess_id=[a-f0-9-]+|[0-9]{2}:[0-9]{2}:[0-9]{2}' | paste - - | sort -k2 | awk '!seen[$1]++{print $2}' | grep -oE '^[0-9]{2}:[0-9]{2}' | uniq -c | tail -40
echo
echo "=== request status codes ==="
grep 'sess_id' access.log | grep -oE '" [0-9]{3} ' | sort | uniq -c
