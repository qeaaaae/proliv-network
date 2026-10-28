#!/usr/bin/env bash
set -uo pipefail
URL="https://sub.proliv-network.xyz/WKA2c2STkbrb5LHf"

echo "=== xray images on main ==="
docker images --format '{{.Repository}}:{{.Tag}}' | grep -iE 'xray|remnawave'

echo "=== fetch + decode links ==="
curl -s --max-time 15 -H "User-Agent: v2rayNG/1.8.5" "$URL" -o /tmp/sub_b64.txt
base64 -d /tmp/sub_b64.txt > /tmp/sub_links.txt 2>/dev/null || base64 -d -i /tmp/sub_b64.txt > /tmp/sub_links.txt
cat /tmp/sub_links.txt | sed -E 's/vless:\/\/([^@]+)@([^:?]+):([0-9]+).*/-> \2:\3/' 

echo "=== build client configs + test each ==="
python3 - <<'PY'
import re, json, base64, urllib.parse
links = [l.strip() for l in open('/tmp/sub_links.txt') if l.strip().startswith('vless://')]
for i, link in enumerate(links):
    u = urllib.parse.urlparse(link)
    q = urllib.parse.parse_qs(u.query)
    host = u.hostname; port = u.port; uid = u.username
    sec = q.get('security',[''])[0]
    name = urllib.parse.unquote(u.fragment or f'link{i}')
    if sec == 'reality':
        stream = {"network":"tcp","security":"reality",
          "realitySettings":{"fingerprint":q.get('fp',['safari'])[0],
            "serverName":q.get('sni',[''])[0],
            "publicKey":q.get('pbk',[''])[0],
            "shortId":q.get('sid',[''])[0],
            "spiderX":q.get('spx',['/'])[0]}}
        flow = q.get('flow',['xtls-rprx-vision'])[0]
    else:
        stream = {"network":"ws","security":"tls",
          "wsSettings":{"path":urllib.parse.unquote(q.get('path',['/'])[0]),
            "headers":{"Host":q.get('host',[host])[0]}},
          "tlsSettings":{"serverName":q.get('sni',[host])[0],
            "fingerprint":q.get('fp',['safari'])[0]}}
        flow = ""
    cfg = {"log":{"loglevel":"warning"},
      "inbounds":[{"listen":"127.0.0.1","port":10900,"protocol":"socks","settings":{"auth":"noauth","udp":True}}],
      "outbounds":[{"protocol":"vless","settings":{"vnext":[{"address":host,"port":port,
          "users":[{"id":uid,"encryption":"none","flow":flow}]}]},
        "streamSettings":stream}]}
    fn = f'/tmp/client_{i}.json'
    open(fn,'w').write(json.dumps(cfg))
    print(i, name, '->', host, port, sec)
PY
