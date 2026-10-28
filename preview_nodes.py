import glob
import json

from bot.handlers.admin.nodes_geo import flag, render_location_block

loc_path = next(p for p in glob.glob("/app/**/locales/ru.json", recursive=True))
texts = json.load(open(loc_path, encoding="utf-8"))


def _(key, **kw):
    return texts[key].format(**kw)


data = json.load(open("/status/status.json", encoding="utf-8"))
blocks = []
for loc in data["groups"]["locations"]:
    cc = loc["flag"].upper()
    s = loc.get("stats") or {}
    header = f"🟢 {flag(cc)} <b>{loc['name']}</b> · {cc}"
    detail = _("admin_nodes_item", load=s.get("load1"), mem=s.get("mem_used_mb"),
               mem_total=s.get("mem_total_mb"), disk=s.get("disk_pct"),
               conns=s.get("conns"), uptime=loc.get("uptime"))
    blocks.append(render_location_block(header, [detail], cc, loc.get("geo"), _))
msg = "\n\n".join(blocks)
print(len(msg))
print(msg)
