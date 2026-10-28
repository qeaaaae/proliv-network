#!/usr/bin/env bash
set -uo pipefail
python3 - <<'PY'
import json, urllib.parse, base64, urllib.request
req=urllib.request.Request('http://127.0.0.1:3444/WKA2c2STkbrb5LHf', headers={'Authorization':'Bearer x'})
raw=urllib.request.urlopen(req,timeout=15).read().decode()
links=[l for l in base64.b64decode(raw).decode().splitlines() if l.startswith('vless://')]
for name in ('de.proliv','uk.proliv','ee-src.proliv','ee.proliv'):
    link=[l for l in links if name in l][0]
    u=urllib.parse.urlparse(link); q=urllib.parse.parse_qs(u.query)
    uuid=u.username; host=u.hostname; port=u.port
    st={'network':q.get('type',['tcp'])[0]}
    sec=q.get('security',['none'])[0]
    if sec=='reality':
        st['security']='reality'
        st['realitySettings']={'serverName':q.get('sni',[''])[0],'publicKey':q.get('pbk',[''])[0],'shortId':q.get('sid',[''])[0],'fingerprint':q.get('fp',['chrome'])[0]}
        flow=q.get('flow',[''])[0]
    elif sec=='tls':
        st['security']='tls'
        st['tlsSettings']={'serverName':q.get('sni',[''])[0],'fingerprint':q.get('fp',['chrome'])[0],'alpn':['http/1.1']}
        flow=''
        st['wsSettings']={'path':urllib.parse.unquote(q.get('path',['/'])[0]),'headers':{'Host':q.get('host',[host])[0]}}
    users={'id':uuid,'encryption':'none'}
    if flow: users['flow']=flow
    conf={
     'log':{'loglevel':'info'},
     'inbounds':[{'tag':'socks','port':10901,'listen':'127.0.0.1','protocol':'socks','settings':{'auth':'noauth','udp':True}}],
     'outbounds':[{'tag':'proxy','protocol':'vless',
       'settings':{'vnext':[{'address':host,'port':port,'users':[users]}]},
       'streamSettings':st}]
    }
    fn='/tmp/ru_'+name.split('.')[0]+'.json'
    open(fn,'w').write(json.dumps(conf))
    print(fn,'ok')
PY
for f in /tmp/ru_*.json; do python3 -c "import json;json.load(open('$f'))" && echo "$f valid"; done
