#!/usr/bin/env bash
set -uo pipefail
echo "=== sub with Happ UA ==="
curl -s "https://sub.proliv-network.xyz/WKA2c2STkbrb5LHf" -H 'User-Agent: Happ/1.2.3' -o /tmp/sub_happ.out
head -c 100 /tmp/sub_happ.out; echo; echo
python3 - <<'PY'
import json
raw=open('/tmp/sub_happ.out','rb').read().decode('utf-8','replace').strip()
try:
    d=json.loads(raw)
except Exception as e:
    print('NOT JSON:',e); raise SystemExit
print('is JSON config')
outs=d.get('outbounds',[])
for o in outs:
    tag=o.get('tag'); proto=o.get('protocol')
    ss=o.get('streamSettings',{})
    fp=(ss.get('realitySettings') or ss.get('tlsSettings') or {}).get('fingerprint')
    frag=(ss.get('sockopt') or {}).get('fragment')
    print(f"{tag} | {proto} | net={ss.get('network')} sec={ss.get('security')} fp={fp} fragment={frag}")
print('routing rules:')
for r_ in d.get('routing',{}).get('rules',[]):
    print(' ',r_)
print('dns:',d.get('dns'))
PY
