#!/usr/bin/env bash
python3 - <<'PY'
import json
d=json.load(open('/tmp/panel_users.json'))
r=d.get('response',d)
us=r.get('users',r if isinstance(r,list) else r.get('items',[]))
u=us[0]
print(json.dumps(u, indent=1)[:2000])
PY
