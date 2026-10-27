#!/usr/bin/env bash
set -u
cd /tmp
echo "=== download Loyalsoldier geo files ==="
curl -sL --max-time 120 -o geosite.dat "https://github.com/Loyalsoldier/v2ray-rules-dat/releases/latest/download/geosite.dat"
curl -sL --max-time 120 -o geoip.dat "https://github.com/Loyalsoldier/v2ray-rules-dat/releases/latest/download/geoip.dat"
ls -la geosite.dat geoip.dat

echo "=== sections present in Loyalsoldier geosite.dat ==="
for s in GEOLOCATION-RU CATEGORY-RU GEOLOCATION-!RU; do
  if grep -ac "$s" geosite.dat >/dev/null 2>&1 && [ "$(grep -ac "$s" geosite.dat)" -gt 0 ]; then echo "$s: PRESENT"; else echo "$s: absent"; fi
done

echo "=== v2fly official geosite.dat (what clients bundle) ==="
curl -sL --max-time 120 -o geosite-v2fly.dat "https://github.com/v2fly/domain-list-community/releases/latest/download/dlc.dat"
ls -la geosite-v2fly.dat
for s in GEOLOCATION-RU CATEGORY-RU; do
  if [ "$(grep -ac "$s" geosite-v2fly.dat)" -gt 0 ]; then echo "$s: PRESENT"; else echo "$s: absent"; fi
done

echo "=== geoip RU check ==="
grep -ac "RU" geoip.dat | head -1

echo "=== browser fetch test ==="
curl -s -o /tmp/browser_resp.txt -w 'code=%{http_code} size=%{size_download}\n' \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36" \
  -H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8" \
  "https://sub.proliv-network.xyz/WKA2c2STkbrb5LHf"
head -c 300 /tmp/browser_resp.txt; echo

echo "=== full responseRules ==="
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
curl -s -H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' -H 'X-Forwarded-Proto: https' \
  "http://127.0.0.1:3443/api/subscription-settings" -o /tmp/subset.json
python3 - <<'PY'
import json
d=json.load(open('/tmp/subset.json'))
r=d.get('response',d) if isinstance(d,dict) else d
rr=r.get('responseRules',{})
print(json.dumps(rr,ensure_ascii=False,indent=1))
PY
