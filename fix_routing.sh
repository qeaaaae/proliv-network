#!/usr/bin/env bash
set -euo pipefail
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
H=(-H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' -H 'X-Forwarded-Proto: https')

python3 - <<'PY'
import json, base64
profile = {
  "Name": "Proliv",
  "GlobalProxy": "true",
  "RemoteDNSType": "DoH",
  "RemoteDNSDomain": "https://dns.google/dns-query",
  "RemoteDNSIP": "8.8.8.8",
  "DomesticDNSType": "DoH",
  "DomesticDNSDomain": "https://common.doh.dns.yandex.net/dns-query",
  "DomesticDNSIP": "77.88.8.8",
  "Geoipurl": "https://github.com/Loyalsoldier/v2ray-rules-dat/releases/latest/download/geoip.dat",
  "Geositeurl": "https://github.com/Loyalsoldier/v2ray-rules-dat/releases/latest/download/geosite.dat",
  "LastUpdated": "",
  "DnsHosts": {"dns.google": "8.8.8.8", "common.doh.dns.yandex.net": "77.88.8.8"},
  "DirectSites": ["geosite:category-ru"],
  "DirectIp": ["geoip:private", "geoip:ru"],
  "ProxySites": [],
  "ProxyIp": [],
  "BlockSites": [],
  "BlockIp": [],
  "DomainStrategy": "IPIfNonMatch",
  "FakeDNS": "false",
  "UseChunkFiles": "true"
}
b64 = base64.b64encode(json.dumps(profile, ensure_ascii=False).encode()).decode()
routing_val = f"happ://routing/onadd/{b64}"

# load current settings, keep everything, swap routing header
d = json.load(open('/tmp/subset.json'))
r = d.get('response', d) if isinstance(d, dict) else d
crh = r.get('customResponseHeaders', {})
crh['routing'] = routing_val
body = {
  "uuid": r.get('uuid'),
  "serveJsonAtBaseSubscription": r.get('serveJsonAtBaseSubscription'),
  "isShowCustomRemarks": r.get('isShowCustomRemarks'),
  "customRemarks": r.get('customRemarks'),
  "customResponseHeaders": crh,
  "randomizeHosts": r.get('randomizeHosts'),
  "responseRules": r.get('responseRules'),
}
open('/tmp/ss_patch.json','w').write(json.dumps(body, ensure_ascii=False))
print('new routing profile written, DirectSites:', profile['DirectSites'])
PY

echo "--- PATCH subscription-settings ---"
curl -s -X PATCH "${H[@]}" -H 'Content-Type: application/json' --data-binary @/tmp/ss_patch.json "$API/subscription-settings" -o /tmp/ss_resp.json
python3 - <<'PY'
import json
d=json.load(open('/tmp/ss_resp.json'))
r=d.get('response',d) if isinstance(d,dict) else d
rt=r.get('customResponseHeaders',{}).get('routing','')
print('routing header now:', rt[:80], '...')
import base64
b64 = rt.split('onadd/')[-1]
dec = json.loads(base64.b64decode(b64))
print('DirectSites =', dec['DirectSites'])
print('Geositeurl =', dec['Geositeurl'])
PY

echo "=== verify via live subscription fetch ==="
curl -s --max-time 15 -H "User-Agent: Happ/1.9.2" -D /tmp/sub_hdrs.txt "https://sub.proliv-network.xyz/WKA2c2STkbrb5LHf" -o /dev/null
grep -i "routing" /tmp/sub_hdrs.txt | head -c 200; echo
