#!/usr/bin/env bash
set -uo pipefail
F=/etc/nginx/sites-available/proliv-tls
python3 - <<'PY'
f='/etc/nginx/sites-available/proliv-tls'
s=open(f).read()
old='''    location /api/xhttp {
        proxy_pass http://127.0.0.1:9444;
        proxy_http_version 1.1;'''
new='''    location /api/xhttp {
        client_max_body_size 0;
        proxy_pass http://127.0.0.1:9444;
        proxy_http_version 1.1;'''
if 'client_max_body_size' not in s:
    s=s.replace(old,new,1)
    open(f,'w').write(s)
    print('patched')
else:
    print('already')
PY
nginx -t && systemctl reload nginx && echo OK
