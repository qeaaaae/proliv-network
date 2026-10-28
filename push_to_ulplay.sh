#!/usr/bin/env bash
set -uo pipefail
# get client config for DE reality link -> /tmp/ru_client.json on main
python3 - <<'PY'
import json, urllib.parse, base64, urllib.request
req=urllib.request.Request('http://127.0.0.1:3444/WKA2c2STkbrb5LHf', headers={'Authorization':'Bearer x'})
raw=urllib.request.urlopen(req,timeout=15).read().decode()
links=[l for l in base64.b64decode(raw).decode().splitlines() if l.startswith('vless://')]
link=[l for l in links if 'de.proliv' in l][0]
u=urllib.parse.urlparse(link); q=urllib.parse.parse_qs(u.query)
uuid=u.username; host=u.hostname; port=u.port
conf={
 'log':{'loglevel':'warning'},
 'inbounds':[{'tag':'socks','port':10901,'listen':'127.0.0.1','protocol':'socks','settings':{'auth':'noauth','udp':True},'sniffing':{'enabled':True,'destOverride':['http','tls']}}],
 'outbounds':[{
   'tag':'proxy','protocol':'vless',
   'settings':{'vnext':[{'address':host,'port':port,'users':[{'id':uuid,'encryption':'none','flow':q.get('flow',[''])[0]}]}]},
   'streamSettings':{'network':'tcp','security':'reality',
     'realitySettings':{'serverName':q.get('sni',[''])[0],'publicKey':q.get('pbk',[''])[0],'shortId':q.get('sid',[''])[0],'fingerprint':q.get('fp',['chrome'])[0]}}
  },{'tag':'direct','protocol':'freedom'}],
 'routing':{'domainStrategy':'AsIs','rules':[{'type':'field','outboundTag':'direct','ip':['geoip:private']}]}
}
open('/tmp/ru_client.json','w').write(json.dumps(conf))
print('conf ok, uuid',uuid[:8],'host',host,'sni',q.get('sni'),'fp',q.get('fp'),'flow',q.get('flow'))
PY
