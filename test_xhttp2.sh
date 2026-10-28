#!/usr/bin/env bash
set -uo pipefail
python3 - <<'PY'
import json, urllib.parse, base64, urllib.request
req=urllib.request.Request('http://127.0.0.1:3444/WKA2c2STkbrb5LHf', headers={'Authorization':'Bearer x'})
raw=urllib.request.urlopen(req,timeout=15).read().decode()
links=[l for l in base64.b64decode(raw).decode().splitlines() if l.startswith('vless://')]
link=[l for l in links if urllib.parse.urlparse(l).hostname=='ee.proliv-network.xyz'][0]
u=urllib.parse.urlparse(link); q=urllib.parse.parse_qs(u.query)
print('using type:',q.get('type'),'path:',q.get('path'))
users={'id':u.username,'encryption':'none'}
st={'network':q.get('type',['tcp'])[0],'security':'tls',
    'tlsSettings':{'serverName':q.get('sni',[''])[0],'fingerprint':q.get('fp',['chrome'])[0],'alpn':['h2','http/1.1']}}
st['xhttpSettings']={'path':urllib.parse.unquote(q.get('path',['/'])[0]),'host':q.get('host',[u.hostname])[0],'mode':q.get('mode',['auto'])[0]}
conf={
 'log':{'loglevel':'info'},
 'inbounds':[{'tag':'socks','port':10903,'listen':'127.0.0.1','protocol':'socks','settings':{'auth':'noauth','udp':True}}],
 'outbounds':[{'tag':'proxy','protocol':'vless',
   'settings':{'vnext':[{'address':u.hostname,'port':u.port,'users':[users]}]},
   'streamSettings':st}]
}
open('/tmp/cfg_xhttp.json','w').write(json.dumps(conf))
PY
docker rm -f xraytest >/dev/null 2>&1
docker run -d --name xraytest --network host -v /tmp/cfg_xhttp.json:/etc/xray/config.json teddysun/xray xray run -c /etc/xray/config.json >/dev/null
sleep 5
for i in 1 2 3; do
  out=$(curl -s --max-time 15 --socks5-hostname 127.0.0.1:10903 https://ifconfig.co/json 2>/dev/null | python3 -c 'import json,sys;print(json.load(sys.stdin)["ip"])' 2>/dev/null)
  [ -n "$out" ] && break
  sleep 3
done
[ -n "$out" ] && echo "XHTTP via CDN: OK exit=$out" || { echo "FAIL"; docker logs xraytest 2>&1 | tail -12; }
docker rm -f xraytest >/dev/null 2>&1
