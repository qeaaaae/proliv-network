#!/usr/bin/env bash
set -uo pipefail
python3 - <<'PY'
import json
d=json.load(open('/tmp/sub_happ.out'))
print('array len:',len(d))
for cfg in d:
    if not isinstance(cfg,dict): continue
    print('=== remarks:',cfg.get('remarks','?'))
    for o in cfg.get('outbounds',[]):
        ss=o.get('streamSettings') or {}
        fp=(ss.get('realitySettings') or ss.get('tlsSettings') or {}).get('fingerprint')
        frag=(ss.get('sockopt') or {}).get('fragment')
        vs=(o.get('settings') or {}).get('vnext') or []
        addr=vs[0].get('address') if vs else '?'
        print(f"  {o.get('tag')} | {o.get('protocol')} | {addr} | net={ss.get('network')} sec={ss.get('security')} fp={fp} frag={json.dumps(frag)}")
PY
