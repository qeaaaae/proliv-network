#!/usr/bin/env python3
"""Rotate viewPosition of enabled ordinary hosts via /api/hosts/actions/reorder.

Every run moves the current first rotating host to the end of the rotating
block, so a different server leads the subscription list. LTE hosts (remark
contains 'LTE'), the pinned last-ordinary host (remark contains 'Казахстан')
and disabled hosts keep their positions.
"""
import json
import sys
import urllib.request

PANEL = "http://localhost:3443"
JWT_PATH = "/root/.panel-jwt"
PINNED_MARKERS = ("LTE", "Казахстан")


def api(method, path, body=None):
    req = urllib.request.Request(
        PANEL + path,
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": "Bearer " + JWT, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.load(r)


JWT = open(JWT_PATH).read().strip()
hosts = api("GET", "/api/hosts").get("response", [])

targets = sorted(
    (
        h
        for h in hosts
        if not h["isDisabled"] and not any(m in h["remark"] for m in PINNED_MARKERS)
    ),
    key=lambda h: h["viewPosition"],
)
if len(targets) < 2:
    sys.exit("nothing to rotate")

positions = sorted(h["viewPosition"] for h in targets)
new_order = targets[1:] + [targets[0]]
new_pos = {h["uuid"]: pos for h, pos in zip(new_order, positions)}

payload = {"hosts": [{"uuid": h["uuid"], "viewPosition": new_pos.get(h["uuid"], h["viewPosition"])} for h in hosts]}
api("POST", "/api/hosts/actions/reorder", payload)

for h in hosts:
    pos = new_pos.get(h["uuid"], h["viewPosition"])
    if h["viewPosition"] != pos:
        print(f'{h["remark"]}: {h["viewPosition"]} -> {pos}')
