---
name: proliv-ip-check
description: Check all ProlivVPN node/edge IPs and domains for RKN blocks via cheburcheck.ru. Use when the user says "проверь айпишники", "прогони айпи", "что заблокировано", or suspects Russian blocking/throttling.
---

# ProlivVPN IP block check

API: `GET https://cheburcheck.ru/api/v1/check?target=<ip-or-domain>` returns JSON
`{blocked, blocked_subnets, ips, rkn_domain, cdn_providers, geo, asn_info}`.
Domains resolve live - pass them as-is, do not hardcode their current IPs.

## Targets

| Target | Role |
|---|---|
| `144.31.240.216` | proliv-main (SE) - panel, landing, bot, cabinet, api, sub, admin, web, www |
| `13.143.192.49` | proliv-node-de (DE) - REALITY :443 + xhttp behind yccdn |
| `31.76.70.98` | proliv-node-ee (EE) - nginx :443 + xhttp behind yccdn, REALITY :10443 (off) |
| `31.76.60.63` | proliv-node-uk (UK) |
| `179.253.82.201` | proliv-node-fi (FI) |
| `87.58.201.121` | proliv-node-nl (NL) - REALITY :443 + socks :8444 (ноды only) |
| `79.183.193.149` | proliv-node-kz (KZ, Актау) - REALITY :443 |
| `de.proliv-network.xyz` | yccdn edge front (LTE DE) |
| `ee.proliv-network.xyz` | yccdn edge front (LTE EE) |
| `de-src.proliv-network.xyz` | DE CDN origin (same IP as node-de) |
| `ee-src.proliv-network.xyz` | EE CDN origin (same IP as node-ee) |

SSH aliases in `~/.ssh/config`: `proliv-main`, `proliv-node-de`, `proliv-node-ee`,
`proliv-node-uk`, `proliv-node-fi`.

## How to run

PowerShell one-liner loop over the table, print
`target => blocked=True/False subnets=[..]`.

Interpretation: report a table clean/blocked; for blocked rows show
`blocked_subnets` and `rkn_domain`. Same flag+country naming as `/check` in the
bot and `/status/status.json` (`flag` field = country code).

## Caveat

cheburcheck = RKN registry only. TSPU behavioral throttling by mobile operators
(shadow-blocking of edge IPs/domains) is NOT in the registry - a clean result
does not rule out throttling; correlate with client-side symptoms.

## Bot command

`/check` (admin-only) in the TG bot does the same plus monthly per-node traffic
from the panel - see `shop/backend/bot/handlers/admin/ip_check.py`.
