#!/usr/bin/env python3
"""Scheduled host hiding for subscription.

Dates are Europe/Moscow. On/after the date the listed hosts get
isHidden=true so users stop seeing them in the subscription.
Idempotent: skips hosts already hidden. Nothing is deleted.

Hosts are matched by UUID (remarks get renamed, uuids don't).
"""
import json, os, sys, urllib.request
from datetime import datetime, timezone, timedelta

PANEL = "http://localhost:3443/api"
KEY = os.popen("grep '^PANEL_API_KEY=' /opt/proliv/shop/.env | cut -d= -f2-").read().strip().strip('"').strip("'").strip('\r')

# uuid -> current remark (for logs only)
SCHEDULE = [
    # 2026-11-27: старая EE (31.76.70.98), LTE Резерв 1 (ee.), LTE Резерв 2 (de.), UK
    ("2026-11-27", [
        ("ae459449-f6ed-4c52-bb66-7ca92f84b9fa", "Эстония Резерв (старая EE)"),
        ("499f8118-d8a0-49f2-becf-9627c0069fb8", "LTE - Резерв 1 (ee.)"),
        ("c492c17a-fd3b-4b44-b173-31f32308606a", "LTE - Резерв 2 (de.)"),
        ("f5738299-a0d1-429d-9cad-3e3d261484bc", "Великобритания"),
    ]),
    # 2026-11-29: Финляндия + FI-LTE (бывший «LTE - Основной»)
    ("2026-11-29", [
        ("a7346d07-5977-4380-aa2f-9905ec5556f1", "Финляндия"),
        ("52805dbb-47a6-4dc6-8856-3acdc98872ea", "LTE - Основной 2 (fi.)"),
    ]),
    # 2026-12-09: Казахстан
    ("2026-12-09", [
        ("1d54d17a-e3b2-4e58-8333-0237fc367da5", "Казахстан"),
    ]),
]

FIELDS = ['remark','address','port','sni','host','path','alpn','fingerprint',
          'inbound','nodes','xhttpExtraParams','sockoptParams','viewPosition',
          'isDisabled','isHidden','securityLayer','mihomoX25519','shuffleHost',
          'overrideSniFromAddress','keepSniBlank','finalMask','serverDescription',
          'muxParams','tags','excludeFromSubscriptionTypes','mapper',
          'internalSquads','xrayJsonTemplateUuid','vlessRouteId',
          'pinnedPeerCertSha256','verifyPeerCertByName','mihomoIpVersion']

def api(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(PANEL + path, data=data, method=method,
        headers={'Authorization': f'Bearer {KEY}', 'Content-Type': 'application/json'})
    return json.loads(urllib.request.urlopen(req, timeout=20).read())

msk = datetime.now(timezone.utc) + timedelta(hours=3)
today = msk.date().isoformat()
print(f"date(MSK)={today}")

hosts = api('GET', '/hosts')['response']
hosts = hosts['hosts'] if isinstance(hosts, dict) else hosts
by_uuid = {h['uuid']: h for h in hosts}

for date, entries in SCHEDULE:
    if today < date:
        continue
    for uuid, label in entries:
        h = by_uuid.get(uuid)
        if not h:
            print(f"  !! host not found: {label} ({uuid})")
            continue
        if h.get('isHidden'):
            print(f"  = already hidden: {h['remark']} ({label})")
            continue
        body = {'uuid': h['uuid']}
        for k in FIELDS:
            if k in h:
                body[k] = h[k]
        body['isHidden'] = True
        api('PATCH', '/hosts', body)
        print(f"  + hidden: {h['remark']} ({label}) since {date}")

sys.exit(0)
