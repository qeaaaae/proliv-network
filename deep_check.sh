#!/usr/bin/env bash
set -uo pipefail
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"
H=(-H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1')

echo '=== NODE DETAIL ==='
for u in b4393e6a-7369-4b93-8dd9-4c5381554544 cefc979e-22dd-40e6-81ee-55141feb01b6 c0ad1fb9-a8f0-469d-aafb-a3be7763d45f; do
curl -s "${H[@]}" "$API/nodes/$u" | python3 -c "
import json,sys
d=json.load(sys.stdin); n=d.get('response',d)
print(n.get('name'),'|',n.get('address'))
for k,v in n.items():
    kl=k.lower()
    if 'inbound' in kl or 'profile' in kl or 'squad' in kl or 'config' in kl:
        print('   ',k,'=',json.dumps(v)[:300])
"
done
echo '=== SQUADS ==='
curl -s "${H[@]}" "$API/internal-squads" | python3 -c "
import json,sys
d=json.load(sys.stdin)
for s in d.get('response',{}).get('internalSquads',d.get('response',[])):
    print(s.get('name'),'| inbounds:',[i.get('tag') for i in s.get('inbounds',[])],'| info:',s.get('info'))
"
