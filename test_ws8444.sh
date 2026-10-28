#!/usr/bin/env bash
set -uo pipefail
python3 - <<'PY'
import json, urllib.parse, base64, urllib.request
req=urllib.request.Request('http://127.0.0.1:3444/WKA2c2STkbrb5LHf', headers={'Authorization':'Bearer x'})
raw=urllib.request.urlopen(req,timeout=15).read().decode()
links=[l for l in base64.b64decode(raw).decode().splitlines() if l.startswith('vless://')]
print('links:',len(links))
for l in links: print(' ', urllib.parse.urlparse(l).hostname, urllib.parse.urlparse(l).port, urllib.parse.parse_qs(urllib.parse.urlparse(l).query).get('type'))
link=[l for l in links if urllib.parse.urlparse(l).port==8444 and 'de.' in urllib.parse.urlparse(l).hostname][0]
u=urllib.parse.urlparse(link); q=urllib.parse.parse_qs(u.query)
conf={
 'log':{'loglevel':'warning'},
 'inbounds':[{'tag':'socks','port':10904,'listen':'127.0.0.1','protocol':'socks','settings':{'auth':'noauth','udp':True}}],
 'outbounds':[{'tag':'proxy','protocol':'vless',
   'settings':{'vnext':[{'address':u.hostname,'port':u.port,'users':[{'id':u.username,'encryption':'none'}]}]},
   'streamSettings':{'network':'ws','security':'tls',
     'tlsSettings':{'serverName':q.get('sni',[u.hostname])[0],'fingerprint':q.get('fp',['chrome'])[0],'alpn':['http/1.1']},
     'wsSettings':{'path':urllib.parse.unquote(q.get('path',['/'])[0]),'headers':{'Host':q.get('host',[u.hostname])[0]}}}}]
}
open('/tmp/cfg_ws8444.json','w').write(json.dumps(conf))
print('config ok')
PY
docker rm -f xraytest >/dev/null 2>&1
docker run -d --name xraytest --network host -v /tmp/cfg_ws8444.json:/etc/xray/config.json teddysun/xray xray run -c /etc/xray/config.json >/dev/null
sleep 4
for i in 1 2 3; do
  out=$(curl -s --max-time 15 --socks5-hostname 127.0.0.1:10904 https://ifconfig.co/json 2>/dev/null | python3 -c 'import json,sys;print(json.load(sys.stdin)["ip"])' 2>/dev/null)
  [ -n "$out" ] && break
  sleep 3
done
[ -n "$out" ] && echo "WS8444 DE: OK exit=$out" || { echo FAIL; docker logs xraytest 2>&1 | tail -10; }
docker rm -f xraytest >/dev/null 2>&1
