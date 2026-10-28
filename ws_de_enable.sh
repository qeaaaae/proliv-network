#!/usr/bin/env bash
set -uo pipefail
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
H=(-H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' -H 'Content-Type: application/json')

# 1. enable WS-CDN inbound on DE + UK nodes
for nu in b4393e6a-7369-4b93-8dd9-4c5381554544 cefc979e-22dd-40e6-81ee-55141feb01b6; do
curl -s "${H[@]}" "$API/nodes/$nu" -o /tmp/n.json
python3 - <<'PY' > /tmp/np.json
import json
n=json.load(open('/tmp/n.json'))['response']
cp=n['configProfile']
ibs=cp.get('activeInbounds',[])
if not any(i['uuid']=='d7b7bf74-239a-45d4-bfdc-b025eb1fa0b6' for i in ibs):
    ibs.append({"uuid":"d7b7bf74-239a-45d4-bfdc-b025eb1fa0b6","profileUuid":"00000000-0000-0000-0000-000000000000"})
cp['activeInbounds']=[{"uuid":i['uuid'],"profileUuid":i['profileUuid']} for i in ibs]
body={k:v for k,v in n.items() if k in ('name','address','port','configProfile','isTrafficTrackingEnabled','isConnected','providerUuid','consumptionMultiplier','isDisabled')}
body['configProfile']=cp
print(json.dumps(body,ensure_ascii=False))
PY
curl -s -X PATCH "${H[@]}" --data @/tmp/np.json "$API/nodes" | python3 -c "import json,sys;n=json.load(sys.stdin).get('response',{});print(n.get('name'),[i['uuid'][:8] for i in n.get('configProfile',{}).get('activeInbounds',[])])"
done

# 2. check nginx /api/ws on DE+UK fallback blocks
echo '--- nginx /api/ws presence ---'
