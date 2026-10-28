import json, urllib.request

JWT = open('/root/.panel-jwt').read().strip()
API = 'http://127.0.0.1:3443/api'

def req(path):
    r = urllib.request.Request(API + path, headers={
        'Authorization': 'Bearer ' + JWT,
        'X-Forwarded-Proto': 'https',
    })
    return json.load(urllib.request.urlopen(r, timeout=20))

print('========== HOSTS ==========')
d = req('/hosts')
r = d.get('response', d)
hosts = r.get('hosts', r.get('items')) if isinstance(r, dict) else r
for h in hosts:
    print(json.dumps({k: h.get(k) for k in (
        'uuid','remark','address','port','path','sni','host','alpn',
        'fingerprint','securityLayer','isDisabled','xhttpExtraParams',
        'nodes','inbound')}, ensure_ascii=False))
    print('---')

print('========== NODES ==========')
d = req('/nodes')
r = d.get('response', d)
nodes = r.get('nodes', r.get('items')) if isinstance(r, dict) else r
for n in nodes:
    cp = n.get('configProfile') or {}
    print(json.dumps({
        'uuid': n.get('uuid'), 'name': n.get('name'), 'address': n.get('address'),
        'consumptionMultiplier': n.get('consumptionMultiplier'),
        'activeConfigProfileUuid': cp.get('activeConfigProfileUuid'),
        'activeInbounds': [(i.get('tag'), i.get('uuid')) for i in cp.get('activeInbounds', [])],
    }, ensure_ascii=False))
    print('---')

print('========== CONFIG PROFILES ==========')
d = req('/config-profiles')
r = d.get('response', d)
profs = r.get('configProfiles', r.get('items')) if isinstance(r, dict) else r
for p in profs:
    print('PROFILE', p.get('name'), p.get('uuid'))
    for i in p.get('inbounds', []):
        keep = {k: i.get(k) for k in ('uuid','tag','port','listen','protocol','network','security')}
        st = i.get('streamSettings') or {}
        if 'xhttpSettings' in st:
            keep['xhttpSettings'] = st['xhttpSettings']
        if 'wsSettings' in st:
            keep['wsSettings'] = st['wsSettings']
        if 'realitySettings' in st:
            rs = st['realitySettings']
            keep['reality'] = {k: rs.get(k) for k in ('dest','serverNames','fingerprint') if k in rs}
        keep['stream_network'] = st.get('network')
        keep['stream_security'] = st.get('security')
        print(' ', json.dumps(keep, ensure_ascii=False))
    print('---')

print('========== SQUADS ==========')
d = req('/internal-squads')
r = d.get('response', d)
sq = r.get('internalSquads', r.get('items')) if isinstance(r, dict) else r
for s in sq:
    print(s.get('name'), s.get('uuid'), 'inbounds:', [(i.get('tag'), i.get('uuid')) for i in s.get('inbounds', [])])
