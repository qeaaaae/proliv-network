#!/usr/bin/env bash
set -uo pipefail
F=/etc/nginx/sites-available/proliv-tls
cp "$F" "$F.bak.$(date +%s)"
python3 - <<'PY'
f='/etc/nginx/sites-available/proliv-tls'
s=open(f).read()
block='''
    # CDN XHTTP route: xray VLESS-XHTTP inbound on 127.0.0.1:9444 (ee via Yandex CDN).
    location /api/xhttp {
        proxy_pass http://127.0.0.1:9444;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
        proxy_buffering off;
    }
'''
if '/api/xhttp' not in s:
    s=s.replace('    location / {', block+'\n    location / {',1)
    open(f,'w').write(s)
    print('added')
else:
    print('already present')
PY
nginx -t && systemctl reload nginx && echo "NGINX OK"
