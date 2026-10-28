#!/usr/bin/env bash
set -uo pipefail
python3 - <<'PY'
import json
conf={
 'log':{'loglevel':'warning'},
 'inbounds':[{'tag':'socks','port':10905,'listen':'127.0.0.1','protocol':'socks','settings':{'auth':'noauth','udp':True}}],
 'outbounds':[{'tag':'proxy','protocol':'vless',
   'settings':{'vnext':[{'address':'de.proliv-network.xyz','port':443,'users':[{'id':'2e3eebc1-500c-43be-aafa-b133112007a4','encryption':'none'}]}]},
   'streamSettings':{'network':'ws','security':'tls',
     'tlsSettings':{'serverName':'de.proliv-network.xyz','fingerprint':'safari','alpn':['http/1.1']},
     'wsSettings':{'path':'/api/ws','headers':{'Host':'de.proliv-network.xyz'}}}}]
}
open('/tmp/cfg_ws443.json','w').write(json.dumps(conf))
PY
docker rm -f xraytest >/dev/null 2>&1
docker run -d --name xraytest --network host -v /tmp/cfg_ws443.json:/etc/xray/config.json teddysun/xray xray run -c /etc/xray/config.json >/dev/null
sleep 4
for i in 1 2 3; do
  out=$(curl -s --max-time 15 --socks5-hostname 127.0.0.1:10905 https://ifconfig.co/json 2>/dev/null | python3 -c 'import json,sys;print(json.load(sys.stdin)["ip"])' 2>/dev/null)
  [ -n "$out" ] && break
  sleep 3
done
[ -n "$out" ] && echo "WS443 fallback DE: OK exit=$out" || { echo FAIL; docker logs xraytest 2>&1 | tail -8; }
docker rm -f xraytest >/dev/null 2>&1
