#!/bin/bash
echo "=== xray uptimes on nodes ==="
for h in 31.76.70.98 31.76.60.63 13.143.192.49 179.253.82.201 87.58.201.121 79.183.193.149; do
  echo "--- $h"
  ssh -i /root/.ssh/backup_ed25519 -o BatchMode=yes -o ConnectTimeout=5 \
    -o StrictHostKeyChecking=accept-new \
    -o UserKnownHostsFile=/opt/proliv/status/known_hosts \
    root@$h 'ps -o etime=,cmd= -C xray 2>/dev/null | head -3; systemctl is-active xray 2>/dev/null; journalctl -u xray --since "24h ago" -o cat 2>/dev/null | grep -ciE "restart|reload"' 2>&1 | head -6
done
echo "=== panel logs (node restarts last 24h) ==="
docker logs remnawave --since 24h 2>&1 | grep -iE 'restart|reload' | grep -ivE 'healthcheck' | tail -10
echo "=== xray restart count in node docker ==="
for h in 31.76.70.98 31.76.60.63 13.143.192.49 179.253.82.201 87.58.201.121 79.183.193.149; do
  echo "--- $h"
  ssh -i /root/.ssh/backup_ed25519 -o BatchMode=yes -o ConnectTimeout=5 \
    -o StrictHostKeyChecking=accept-new \
    -o UserKnownHostsFile=/opt/proliv/status/known_hosts \
    root@$h 'docker ps --format "{{.Names}} {{.Status}}" 2>/dev/null | head -4' 2>&1 | head -5
done
