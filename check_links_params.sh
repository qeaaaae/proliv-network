#!/usr/bin/env bash
set -uo pipefail
docker rm -f xraytest xray-client-test >/dev/null 2>&1 || true
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
SUB=$(curl -s "http://127.0.0.1:3444/WKA2c2STkbrb5LHf" -H "Authorization: Bearer x" || true)
echo "$SUB" | base64 -d 2>/dev/null | grep '^vless' | python3 -c "
import sys, urllib.parse
for line in sys.stdin:
    line=line.strip()
    if not line: continue
    u=urllib.parse.urlparse(line)
    q=urllib.parse.parse_qs(u.query)
    print(u.hostname, '|', 'type='+q.get('type',['?'])[0], 'sec='+q.get('security',['?'])[0], 'fp='+q.get('fp',['?'])[0], 'sni='+q.get('sni',['?'])[0], 'sid='+q.get('sid',['?'])[0], 'pbk='+q.get('pbk',['?'])[0][:12], 'path='+q.get('path',['?'])[0])
"
