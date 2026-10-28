"""ipregion geo block for the admin /nodes command (data: status-probe -> status.json `geo`)."""

import html
import re
import time
from collections.abc import Callable, Mapping

_CC_RE = re.compile(r"^([A-Z]{2})\b")

ICON_MISMATCH = '<tg-emoji emoji-id="5883955653348692941">🗺</tg-emoji>'
ICON_BLOCKED = '<tg-emoji emoji-id="5872829476143894491">🚫</tg-emoji>'
ICON_CDN = '<tg-emoji emoji-id="5877465816030515018">🔗</tg-emoji>'

# ipregion custom-service name -> display name (missing = shown as is)
_CUSTOM_NAMES: dict[str, str] = {
    "Gemini Supported": "Gemini",
    "Disney+ Access": "Disney+",
    "Ookla Speedtest": "Speedtest",
}
# names with localized wording
_CUSTOM_NAME_KEYS: dict[str, str] = {
    "Reddit (Guest Access)": "admin_nodes_geo_reddit_guest",
    "Spotify Signup": "admin_nodes_geo_spotify_signup",
}
_BLOCKED_VALUES = {"No", "Denied"}


def flag(cc: str) -> str:
    cc = cc.upper()
    if len(cc) != 2 or not cc.isalpha():
        return ""
    return "".join(chr(0x1F1E6 + ord(c) - ord("A")) for c in cc)


def _cc(value: object) -> str | None:
    match = _CC_RE.match(value) if isinstance(value, str) else None
    return match.group(1) if match else None


def _group(geo: Mapping[str, object], name: str) -> dict[str, object]:
    raw = geo.get(name)
    return {str(k): v for k, v in raw.items()} if isinstance(raw, dict) else {}


def render_location_block(
    header: str,
    details: list[str],
    cc: str,
    geo: Mapping[str, object] | None,
    gettext: Callable[..., str],
) -> str:
    """One server = one <blockquote>: header, metrics, then the ipregion geo lines."""
    lines = [header, *details]
    if geo:
        lines.extend(_geo_lines(cc, geo, gettext))
    return "<blockquote>" + "\n".join(lines) + "</blockquote>"


def _geo_lines(cc: str, geo: Mapping[str, object], gettext: Callable[..., str]) -> list[str]:
    def custom_name(service: str) -> str:
        key = _CUSTOM_NAME_KEYS.get(service)
        return gettext(key) if key else _CUSTOM_NAMES.get(service, service)

    others: dict[str, list[str]] = {}
    for service, value in _group(geo, "primary").items():
        seen = _cc(value)
        if seen and seen != cc and value == seen:
            svc = html.escape(service)
            others.setdefault(seen, []).append(f'<a href="https://{svc}">{svc}</a>')

    blocked: list[str] = []
    for service, value in _group(geo, "custom").items():
        if value in _BLOCKED_VALUES:
            label = html.escape(custom_name(service))
            if label not in blocked:
                blocked.append(label)
            continue
        seen = _cc(value)
        if seen and seen != cc and value == seen:
            others.setdefault(seen, []).append(html.escape(custom_name(service)))

    cdn = []
    for service, value in _group(geo, "cdn").items():
        seen = _cc(value)
        if seen:
            label = html.escape(service.removesuffix(" CDN"))
            cdn.append(f"{label} {flag(seen)} {seen}")

    lines: list[str] = []
    if others:
        lines.append(f"{ICON_MISMATCH} {gettext('admin_nodes_geo_mismatch')}")
        for country, items in sorted(others.items(), key=lambda kv: -len(kv[1])):
            lines.append(f"{flag(country)} {country}: {', '.join(items)}")
    else:
        lines.append(f"{ICON_MISMATCH} {gettext('admin_nodes_geo_all_match', cc=cc)}")
    if blocked:
        text = gettext("admin_nodes_geo_blocked", items=", ".join(blocked))
        lines.append(f"{ICON_BLOCKED} {text}")
    if cdn:
        lines.append(f"{ICON_CDN} CDN: {' · '.join(cdn)}")
    checked = geo.get("checked_at")
    if isinstance(checked, int) and checked > 0:
        stamp = time.strftime("%d.%m %H:%M", time.gmtime(checked))
        lines.append(f"<i>{gettext('admin_nodes_geo_checked', stamp=stamp)}</i>")
    return lines
