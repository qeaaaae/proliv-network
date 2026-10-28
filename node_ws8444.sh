#!/usr/bin/env bash
set -uo pipefail
# $1 = node domain (de./uk./ee.), run on the node
DOM="$1"
cat > /etc/nginx/sites-available/proliv-ws <<EOF
# VLESS-WS-TLS backup route (DPI-safe: real TLS + real LE cert, no CDN).
server {
    listen 8444 ssl;
    server_name $DOM;

    ssl_certificate     /etc/letsencrypt/live/$DOM/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOM/privkey.pem;

    location /api/ws {
        proxy_pass http://127.0.0.1:9443;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Forwarded-For \$remote_addr;
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
        proxy_buffering off;
    }

    location / { return 404; }
}
EOF
ln -sf /etc/nginx/sites-available/proliv-ws /etc/nginx/sites-enabled/proliv-ws
nginx -t && systemctl reload nginx
ufw allow 8444/tcp >/dev/null 2>&1; ufw status | grep 8444
echo "listening:"; ss -tlnp | grep 8444 || netstat -tlnp 2>/dev/null | grep 8444
