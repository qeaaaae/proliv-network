#!/usr/bin/env bash
set -euo pipefail
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
H=(-H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' -H 'X-Forwarded-Proto: https')

curl -s "${H[@]}" "$API/subscription-settings" -o /tmp/subset.json
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
  "Geoipurl": "https://proliv-network.xyz/status-data/geoip.dat",
  "Geositeurl": "https://proliv-network.xyz/status-data/geosite.dat",
  "LastUpdated": "",
  "DnsHosts": {"dns.google": "8.8.8.8", "common.doh.dns.yandex.net": "77.88.8.8"},
  "DirectSites": ["geosite:category-ru"],
  "DirectIp": ["geoip:private"],
  "ProxySites": [],
  "ProxyIp": [],
  "BlockSites": [],
  "BlockIp": [],
  "DomainStrategy": "IPIfNonMatch",
  "FakeDNS": "false",
  "UseChunkFiles": "true"
}
b64 = base64.b64encode(json.dumps(profile, ensure_ascii=False).encode()).decode()
d = json.load(open('/tmp/subset.json'))
r = d.get('response', d) if isinstance(d, dict) else d
crh = r.get('customResponseHeaders', {})
crh['routing'] = f"happ://routing/onadd/{b64}"
body = {
  "uuid": r.get('uuid'),
  "serveJsonAtBaseSubscription": r.get('serveJsonAtBaseSubscription'),
  "isShowCustomRemarks": r.get('isShowCustomRemarks'),
  "customRemarks": r.get('customRemarks'),
  "customResponseHeaders": crh,
  "randomizeHosts": r.get('randomizeHosts'),
  "responseRules": r.get('responseRules'),
}
open('/tmp/ss_patch4.json','w').write(json.dumps(body, ensure_ascii=False))
print('DirectIp ->', profile['DirectIp'])
PY

curl -s -X PATCH "${H[@]}" -H 'Content-Type: application/json' --data-binary @/tmp/ss_patch4.json "$API/subscription-settings" -o /dev/null

echo "=== verify live ==="
curl -s --max-time 15 -H "User-Agent: Happ/1.9.2" -D /tmp/h2.txt "https://sub.proliv-network.xyz/WKA2c2STkbrb5LHf" -o /dev/null
grep -i routing /tmp/h2.txt | python3 -c "
import sys,base64,json
b64=sys.stdin.read().split('onadd/')[-1].strip()
p=json.loads(base64.b64decode(b64))
print('DirectSites:',p['DirectSites'])
print('DirectIp:',p['DirectIp'])
"
