#!/usr/bin/env bash
set -uo pipefail
# extract each config from array, save separately
python3 - <<'PY'
import json
d=json.load(open('/tmp/sub_happ.out'))
for cfg in d:
    r=cfg.get('remarks','x')
    name='de' if 'Герман' in r else 'uk' if 'Велико' in r else 'ee-src' if 'Эстония' in r and 'LTE' not in r else 'lte'
    cfg['log']={'loglevel':'warning'}
    cfg['inbounds']=[{'tag':'socks','port':10902,'listen':'127.0.0.1','protocol':'socks','settings':{'auth':'noauth','udp':True}}]
    open('/tmp/cfg_'+name+'.json','w').write(json.dumps(cfg))
    print(name,'written')
PY
