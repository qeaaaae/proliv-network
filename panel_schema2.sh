#!/bin/bash
python3 - <<'PY'
import json
spec = json.load(open('/tmp/openapi.json'))
paths = spec.get('paths', {})
for p, ops in sorted(paths.items()):
    for m in ops:
        if any(k in p for k in ('config-profile', 'host', 'node', 'squad', 'inbound')):
            print(m.upper(), p)
PY
