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
import subprocess
import time
import urllib.request

OUT_DIR = "/opt/proliv/status"
OUT_FILE = os.path.join(OUT_DIR, "status.json")
# поминутная история - не публичная (OUT_DIR отдаётся через nginx)
STATE_FILE = "/opt/proliv/.status-state.json"
SHOP_ENV = "/opt/proliv/shop/.env"
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


SSH_KEY = "/root/.ssh/backup_ed25519"
SSH_KNOWN_HOSTS = "/opt/proliv/status/known_hosts"
NODE_STATS_CMD = (
    "cat /proc/loadavg; "
    "free -m | awk '/Mem:/{print $3, $2}'; "
    "df --output=pcent / | tail -1; "
    "ss -tn state established | wc -l; "
    # ipregion (infra/ipregion-node-install.sh) - гео-проверка IP ноды раз в 6ч
    "echo __GEO__; stat -c %Y /opt/ipregion/last.json 2>/dev/null; "
    "cat /opt/ipregion/last.json 2>/dev/null"
)


def parse_geo(raw):
    """mtime + ipregion JSON -> compact {checked_at, primary/custom/cdn: {service: ipv4}} без IP."""
    try:
        mtime, body = raw.split("\n", 1)
        results = json.loads(body)["results"]
        return {
            "checked_at": int(mtime),
            **{
                group: {r["service"]: r.get("ipv4") for r in results.get(group, [])}
                for group in ("primary", "custom", "cdn")
            },
        }
    except (ValueError, KeyError, TypeError):
        return None


def node_stats(host):
    """SSH probe: load/mem/disk/conn count (+ ipregion geo) on a VPN node (backup key, read-only)."""
    try:
        p = subprocess.run(
            [
                "ssh", "-i", SSH_KEY, "-o", "BatchMode=yes",
                "-o", "ConnectTimeout=5",
                "-o", "StrictHostKeyChecking=accept-new",
                "-o", f"UserKnownHostsFile={SSH_KNOWN_HOSTS}",
                f"root@{host}", NODE_STATS_CMD,
            ],
            capture_output=True, text=True, timeout=20,
        )
        if p.returncode != 0:
            return None, None
        head, _, geo_raw = p.stdout.partition("__GEO__\n")
        lines = [l.strip() for l in head.strip().splitlines() if l.strip()]
        load1 = float(lines[0].split()[0])
        mem_used, mem_total = (int(x) for x in lines[1].split()[:2])
        return {
            "load1": load1,
            "mem_used_mb": mem_used,
            "mem_total_mb": mem_total,
            "disk_pct": int(lines[2].rstrip("%")),
            "conns": int(lines[3]),
        }, parse_geo(geo_raw)
    except Exception:
        return None, None


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


def _tg_config():
    tok = cid = None
    try:
        with open(SHOP_ENV, encoding="utf-8") as f:
            for line in f:
                if line.startswith("BOT_TOKEN="):
                    tok = line.split("=", 1)[1].strip().strip('"')
                elif line.startswith("BOOTSTRAP_OWNER_TELEGRAM_ID="):
                    cid = line.split("=", 1)[1].strip().strip('"')
    except OSError:
        pass
    return tok, cid


def tg_send(text: str) -> None:
    tok, cid = _tg_config()
    if not tok or not cid:
        return
    try:
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{tok}/sendMessage",
            data=json.dumps({"chat_id": int(cid), "text": text}).encode(),
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=10)
    except Exception:
        pass


def load():
    for p in (STATE_FILE, OUT_FILE):  # OUT_FILE - миграция со старого формата
        try:
            with open(p, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            continue
    return {"samples": {}}


def main():
    now_min = int(time.time() // 60)
    data = load()
    samples = data.get("samples", {})

    results = {}
    for t in TARGETS:
        results[t["id"]] = check(t)
    probes = {t["id"]: node_stats(t["host"]) for t in TARGETS if t["kind"] == "location"}
    stats = {tid: p[0] for tid, p in probes.items()}
    geo = {tid: p[1] for tid, p in probes.items()}
    samples[str(now_min)] = results

    # TG-алерты админу: шлём только на устойчивой смене состояния (2 мин подряд)
    streak = data.get("streak", {})
    alerted = data.get("alerted", {})
    for t in TARGETS:
        tid = t["id"]
        now = results[tid]
        last, cnt = streak.get(tid, [None, 0])
        cnt = cnt + 1 if last == now else 1
        streak[tid] = [now, cnt]
        was = alerted.get(tid)
        if was is None:
            alerted[tid] = now
        elif now != was and cnt >= 2:
            mark = "🟢" if now else "🔴"
            msg = "доступна снова" if now else "НЕДОСТУПНА"
            tg_send(f"{mark} Proliv Network: {t['name']} - {msg}")
            alerted[tid] = now

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
        if stats.get(tid):
            entry["stats"] = stats[tid]
        if geo.get(tid):
            entry["geo"] = geo[tid]
        if t.get("flag"):
            entry["flag"] = t["flag"]
        if t.get("icon"):
            entry["icon"] = t["icon"]
        out["groups"][t["group"]].append(entry)

    out["all_up"] = all_up

    os.makedirs(OUT_DIR, exist_ok=True)
    # приватное состояние (полная поминутная история) - отдельно от публичного выхлопа
    tmp_state = STATE_FILE + ".tmp"
    with open(tmp_state, "w", encoding="utf-8") as f:
        json.dump({"samples": samples, "streak": streak, "alerted": alerted}, f)
    os.replace(tmp_state, STATE_FILE)

    tmp = OUT_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    os.replace(tmp, OUT_FILE)


if __name__ == "__main__":
    main()
