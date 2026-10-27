#!/bin/bash
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130.0 Safari/537.36'
for u in \
  "https://proliv-network.xyz/" \
  "https://www.proliv-network.xyz/" \
  "https://app.proliv-network.xyz/" \
  "https://panel.proliv-network.xyz/" \
  "https://sub.proliv-network.xyz/-_9jFSnmwY9NBaCP" \
  "https://uk.proliv-network.xyz/" \
  "https://de.proliv-network.xyz/" \
  "https://ee.proliv-network.xyz/"; do
  curl -sk -o /dev/null -w "$u -> %{http_code}\n" --max-time 10 -A "$UA" -H 'Accept: text/html' "$u"
done
curl -sk -o /dev/null -w "sub raw sub -> %{http_code}\n" --max-time 10 "https://sub.proliv-network.xyz/-_9jFSnmwY9NBaCP"
BT=$(grep -E '^BOT_TOKEN=' /opt/proliv/shop/.env | cut -d= -f2-)
curl -s --max-time 10 "https://api.telegram.org/bot$BT/getWebhookInfo" | python3 -c "import sys,json; r=json.load(sys.stdin)['result']; print('webhook:',r['url'],'| pending:',r['pending_update_count'],'| err:',r.get('last_error_message','-'))"
docker ps --format '{{.Names}} {{.Status}}' | grep -vc 'healthy\|Up' | xargs echo "unhealthy_count(~):"
docker ps --format '{{.Names}}' | wc -l | xargs echo "containers:"
pgrep -c cloudflared 2>/dev/null || echo "cloudflared: 0"
