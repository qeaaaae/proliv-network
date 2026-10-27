#!/bin/bash
echo "=== proliv.env state ==="
grep -nE '^SUBPAGE_API_TOKEN=' /opt/proliv/proliv.env | sed 's/=\(.\{0,4\}\).*/=\1.../'
grep -cE '^[A-Za-z_]+=' /opt/proliv/proliv.env | xargs echo "keyed lines:"
grep -vE '^[A-Za-z_]+=|^#|^$' /opt/proliv/proliv.env | sed 's/\(.\{0,12\}\).*/STRAY: \1.../'
echo "=== compose subpage token check ==="
cd /opt/proliv && docker compose --env-file proliv.env config 2>/dev/null | grep 'REMNAWAVE_API_TOKEN' | sed 's/=\(.\{0,10\}\).*/=\1.../'
echo "=== webhook ==="
BT=$(grep -E '^BOT_TOKEN=' /opt/proliv/shop/.env | cut -d= -f2-)
curl -s --max-time 10 "https://api.telegram.org/bot$BT/getWebhookInfo" | python3 -c "import sys,json; r=json.load(sys.stdin).get('result',{}); print('url:',r.get('url')); print('last_err:',r.get('last_error_message','-'))"
echo "=== bot logs tail ==="
docker logs remnawave-minishop-bot --since 15m 2>&1 | grep -iE 'webhook|error' | tail -5
