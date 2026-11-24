#!/usr/bin/env python3
"""Rotate viewPosition of enabled ordinary hosts via /api/hosts/actions/reorder.

Rules (subscription order):
- Rotation unit = location group: a reserve host ("... Резерв") is glued right
  after its regular host and never floats above it. Groups rotate, hosts
  inside a group keep main -> reserve order.
- Pinned: hosts with 'LTE' or 'Казахстан' in remark never join rotation.
  LTE hosts are additionally re-sorted every run: mains first strictly by
  number (Основной, Основной 2, ...), then reserves by number.
- Disabled/hidden hosts keep their positions.
"""
import json
import re
import sys
import urllib.request

PANEL = "http://localhost:3443"
JWT_PATH = "/root/.panel-jwt"
PINNED_MARKERS = ("LTE", "Казахстан")
RESERVE_SUFFIX = " Резерв"


def api(method, path, body=None):
    req = urllib.request.Request(
        PANEL + path,
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": "Bearer " + JWT, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.load(r)


def lte_sort_key(h):
    remark = h["remark"]
    is_reserve = "Резерв" in remark
    nums = re.findall(r"\d+", remark)
    num = int(nums[-1]) if nums else 1
    return (1 if is_reserve else 0, num)


JWT = open(JWT_PATH).read().strip()
hosts = api("GET", "/api/hosts").get("response", [])

rotating = [
    h for h in hosts
    if not h["isDisabled"] and not h.get("isHidden")
    and not any(m in h["remark"] for m in PINNED_MARKERS)
]
pinned = [h for h in hosts if h not in rotating]

# --- group rotating hosts: base remark (strip " Резерв") -> [main, *reserves]
groups = {}
for h in rotating:
    base = h["remark"][:-len(RESERVE_SUFFIX)] if h["remark"].endswith(RESERVE_SUFFIX) else h["remark"]
    groups.setdefault(base, []).append(h)
for members in groups.values():
    members.sort(key=lambda h: (h["remark"].endswith(RESERVE_SUFFIX), h["viewPosition"]))

# order groups by current position, rotate left by one group
ordered_groups = sorted(groups.values(), key=lambda ms: min(h["viewPosition"] for h in ms))
if len(ordered_groups) > 1:
    ordered_groups = ordered_groups[1:] + ordered_groups[:1]
flat = [h for ms in ordered_groups for h in ms]

positions = sorted(h["viewPosition"] for h in flat)
new_pos = {h["uuid"]: pos for h, pos in zip(flat, positions)}

# --- LTE pinned hosts: enforce mains-then-reserves numeric order
lte_hosts = sorted(
    (h for h in pinned if "LTE" in h["remark"]),
    key=lte_sort_key,
)
lte_positions = sorted(h["viewPosition"] for h in lte_hosts)
for h, pos in zip(lte_hosts, lte_positions):
    new_pos[h["uuid"]] = pos

payload = {"hosts": [{"uuid": h["uuid"], "viewPosition": new_pos.get(h["uuid"], h["viewPosition"])} for h in hosts]}
api("POST", "/api/hosts/actions/reorder", payload)

for h in hosts:
    pos = new_pos.get(h["uuid"], h["viewPosition"])
    if h["viewPosition"] != pos:
        print(f'{h["remark"]}: {h["viewPosition"]} -> {pos}')
