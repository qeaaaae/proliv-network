#!/bin/bash
# Add /api/ws WS proxy to TLS fallback block on EE node + reload nginx.
set -e
CONF=/etc/nginx/sites-enabled/proliv-tls

if grep -q 'location /api/ws' "$CONF"; then
  echo "already present"
else
  cp "$CONF" "${CONF}.bak.$(date +%s)"
  python3 - <<'PY'
conf = open('/etc/nginx/sites-enabled/proliv-tls').read()
block = '''
    # CDN WS route: xray VLESS-WS inbound on 127.0.0.1:9443 (ee via Yandex CDN).
    location /api/ws {
        proxy_pass http://127.0.0.1:9443;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
        proxy_buffering off;
    }
'''
conf = conf.replace('    location / {', block + '\n    location / {', 1)
open('/etc/nginx/sites-enabled/proliv-tls', 'w').write(conf)
print('inserted ws location')
PY
fi

nginx -t && systemctl reload nginx
echo "== xray ws listener =="
sleep 2
ss -tlnp | grep 9443 || echo "9443 not bound yet"
echo "== ws path through nginx:8443 =="
curl -sk -o /dev/null -w "GET /api/ws -> %{http_code}\n" --resolve ee.proliv-network.xyz:8443:127.0.0.1 https://ee.proliv-network.xyz:8443/api/ws
curl -sk -o /dev/null -w "GET / -> %{http_code}\n" --resolve ee.proliv-network.xyz:8443:127.0.0.1 https://ee.proliv-network.xyz:8443/
