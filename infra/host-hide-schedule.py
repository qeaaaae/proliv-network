#!/usr/bin/env python3
"""Scheduled host hiding for subscription.

Dates are Europe/Moscow. On/after the date the listed hosts get
isHidden=true so users stop seeing them in the subscription.
Idempotent: skips hosts already hidden. Nothing is deleted.
"""
import json, os, sys, urllib.request
from datetime import datetime, timezone, timedelta

PANEL = "http://localhost:3443/api"
KEY = os.popen("grep '^PANEL_API_KEY=' /opt/proliv/shop/.env | cut -d= -f2-").read().strip().strip('"').strip("'").strip('\r')

SCHEDULE = [
    ("2026-11-27", ["🇪🇪 Эстония", "🇪🇺 LTE - Резерв 1", "🇪🇺 LTE - Резерв 2", "🇬🇧 Великобритания"]),
    ("2026-11-29", ["🇫🇮 Финляндия", "🇪🇺 LTE - Основной"]),
    ("2026-12-09", ["🇰🇿 Казахстан"]),
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
by_remark = {h['remark']: h for h in hosts}

changed = False
for date, remarks in SCHEDULE:
    if today < date:
        continue
    for remark in remarks:
        h = by_remark.get(remark)
        if not h:
            print(f"  !! host not found: {remark}")
            continue
        if h.get('isHidden'):
            print(f"  = already hidden: {remark}")
            continue
        body = {'uuid': h['uuid']}
        for k in FIELDS:
            if k in h:
                body[k] = h[k]
        body['isHidden'] = True
        api('PATCH', '/hosts', body)
        print(f"  + hidden: {remark} (since {date})")
        changed = True

sys.exit(0)
