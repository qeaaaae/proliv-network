#!/usr/bin/env python3
"""Proliv status probe: real uptime for the /status page.

Runs every minute via systemd timer. Checks:
  - VPN nodes: TCP connect to <node>:443 (Reality endpoint liveness)
  - services: HTTP GET on localhost ports
Keeps a rolling 24h history in /opt/proliv/status/status.json and emits
48 half-hour slots per target for the landing to render.
"""
import json
import os
import socket
import time
import urllib.request

OUT_DIR = "/opt/proliv/status"
OUT_FILE = os.path.join(OUT_DIR, "status.json")
HISTORY_MIN = 24 * 60          # keep 24h of per-minute samples
SLOTS = 48                     # half-hour slots rendered by the page
TIMEOUT = 5

# kind=location -> TCP check; kind=service -> HTTP check
TARGETS = [
    {"id": "ee", "kind": "location", "group": "locations", "name": "Эстония · Таллин",
     "flag": "ee", "host": "31.76.70.98", "port": 443},
    {"id": "uk", "kind": "location", "group": "locations", "name": "Великобритания · Лондон",
     "flag": "gb", "host": "31.76.60.63", "port": 443},
    {"id": "de", "kind": "location", "group": "locations", "name": "Германия · Франкфурт",
     "flag": "de", "host": "13.143.192.49", "port": 443},
    {"id": "bot", "kind": "service", "group": "services", "name": "Telegram-бот",
     "icon": "tg", "url": "http://127.0.0.1:8088/healthz"},
    {"id": "cabinet", "kind": "service", "group": "services", "name": "Личный кабинет",
     "icon": "cab", "url": "http://127.0.0.1:8082/"},
]


def check(t):
    if t["kind"] == "location":
        try:
            with socket.create_connection((t["host"], t["port"]), timeout=TIMEOUT):
                return True
        except OSError:
            return False
    try:
        req = urllib.request.Request(t["url"], headers={"User-Agent": "proliv-status/1"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return 200 <= r.status < 500
    except Exception:
        return False


def load():
    try:
        with open(OUT_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"samples": {}}


def main():
    now_min = int(time.time() // 60)
    data = load()
    samples = data.get("samples", {})

    results = {}
    for t in TARGETS:
        results[t["id"]] = check(t)
    samples[str(now_min)] = results

    # trim to last 24h
    cutoff = now_min - HISTORY_MIN
    samples = {k: v for k, v in samples.items() if int(k) >= cutoff}

    out = {"updated_at": int(time.time()), "groups": {"locations": [], "services": []}}
    all_up = True
    for t in TARGETS:
        tid = t["id"]
        # per-minute series for this target (missing sample = unknown)
        series = []
        for m in range(now_min - HISTORY_MIN + 1, now_min + 1):
            s = samples.get(str(m))
            series.append(None if s is None or tid not in s else bool(s[tid]))
        known = [x for x in series if x is not None]
        pct = round(100.0 * sum(known) / len(known)) if known else None

        # 48 half-hour slots: ok >=95% up, degraded >=50%, else down; empty -> -1
        slot_len = HISTORY_MIN // SLOTS  # 30 min
        slots = []
        for i in range(SLOTS):
            chunk = series[i * slot_len:(i + 1) * slot_len]
            vals = [x for x in chunk if x is not None]
            if not vals:
                slots.append(-1)
                continue
            ratio = sum(vals) / len(vals)
            slots.append(0 if ratio >= 0.95 else (1 if ratio >= 0.5 else 2))

        up = bool(series[-1])
        all_up = all_up and up
        entry = {
            "id": tid,
            "name": t["name"],
            "up": up,
            "state": "Работает" if up else "Недоступен",
            "uptime": f"{pct}%" if pct is not None else "—",
            "slots": slots,
        }
        if t.get("flag"):
            entry["flag"] = t["flag"]
        if t.get("icon"):
            entry["icon"] = t["icon"]
        out["groups"][t["group"]].append(entry)

    out["all_up"] = all_up
    out["samples"] = samples

    os.makedirs(OUT_DIR, exist_ok=True)
    tmp = OUT_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    os.replace(tmp, OUT_FILE)


if __name__ == "__main__":
    main()
