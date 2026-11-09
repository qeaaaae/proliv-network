"""Admin /check: IP block status via cheburcheck + monthly per-node traffic."""

import asyncio
import html
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import aiohttp
from aiogram import Router, types
from aiogram.filters import Command

from bot.handlers.admin.nodes_geo import flag
from bot.middlewares.i18n import JsonI18n
from bot.services.lte_traffic_alert_worker import watched_node_uuids
from bot.services.panel_api_service import PanelApiService
from config.settings import Settings

logger = logging.getLogger(__name__)

router = Router(name="admin_ip_check_router")

STATUS_FILE = Path("/status/status.json")
CHEBURCHECK_URL = "https://cheburcheck.ru/api/v1/check"
CHECK_TIMEOUT = aiohttp.ClientTimeout(total=15)

CDN_TARGETS = (
    ("de.proliv-network.xyz", "CDN de"),
    ("ee.proliv-network.xyz", "CDN ee"),
    ("api.proliv-network.xyz", "main api"),
)

# status.json locations carry no "host" - node IPs are static infra facts.
NODE_IPS = {
    "ee": "31.76.70.98",
    "uk": "31.76.60.63",
    "de": "13.143.192.49",
    "fi": "179.253.82.201",
    "nl": "87.58.201.121",
    "kz": "79.183.193.149",
}


def _node_flag(node_name: str, country_code: str, flag_by_id: dict[str, str]) -> str:
    prefix = node_name.split("-")[0].strip().lower()[:2] if node_name else ""
    if prefix in flag_by_id:
        return flag(flag_by_id[prefix])
    if country_code and country_code.upper() != "XX":
        return flag(country_code)
    return "🌐"


async def _check_one(
    session: aiohttp.ClientSession, target: str
) -> dict[str, Any] | None:
    try:
        async with session.get(CHEBURCHECK_URL, params={"target": target}) as resp:
            if resp.status != 200:
                return None
            data = await resp.json(content_type=None)
            return data if isinstance(data, dict) else None
    except (aiohttp.ClientError, asyncio.TimeoutError):
        return None


async def _check_all(
    session: aiohttp.ClientSession, targets: list[str]
) -> list[dict[str, Any] | None]:
    # cheburcheck 429s on bursts - go sequential with a pause between calls.
    results: list[dict[str, Any] | None] = []
    for i, target in enumerate(targets):
        if i:
            await asyncio.sleep(2)
        result = await _check_one(session, target)
        if result is None:
            await asyncio.sleep(4)
            result = await _check_one(session, target)
        results.append(result)
    return results


@router.message(Command("check"))
async def ip_check_command_handler(
    message: types.Message,
    settings: Settings,
    i18n_data: dict,
    panel_service: PanelApiService,
) -> None:
    current_lang = i18n_data.get("current_language", settings.DEFAULT_LANGUAGE)
    i18n: JsonI18n | None = i18n_data.get("i18n_instance")
    if not i18n:
        await message.answer("Language service error.")
        return
    _ = lambda key, **kwargs: i18n.gettext(current_lang, key, **kwargs)

    targets: list[tuple[str, str, str]] = []
    flag_by_id: dict[str, str] = {}
    try:
        raw = await asyncio.to_thread(STATUS_FILE.read_text, encoding="utf-8")
        data = json.loads(raw)
        for loc in data.get("groups", {}).get("locations", []):
            loc_id = str(loc.get("id") or "").strip().lower()
            flag_by_id[loc_id] = str(loc.get("flag") or "")
            host = str(loc.get("host") or "").strip() or NODE_IPS.get(loc_id, "")
            if host:
                targets.append(
                    (str(loc.get("flag") or ""), str(loc.get("name") or host), host)
                )
    except (OSError, ValueError) as exc:
        logger.warning("ip check: cannot read %s: %s", STATUS_FILE, exc)

    for domain, label in CDN_TARGETS:
        targets.append(("", label, domain))

    if not targets:
        await message.answer(_("admin_ipcheck_no_targets"))
        return

    progress = await message.answer(_("admin_ipcheck_progress"))

    async with aiohttp.ClientSession(timeout=CHECK_TIMEOUT) as session:
        results = await _check_all(session, [target for _, _, target in targets])

    lines = [f"<b>{_('admin_ipcheck_header')}</b>"]
    for (country, name, target), result in zip(targets, results):
        icon = flag(country) if country else "🌐"
        if result is None:
            status = _("admin_ipcheck_err")
        elif result.get("blocked"):
            status = _("admin_ipcheck_blocked")
        else:
            status = _("admin_ipcheck_ok")
        lines.append(
            _(
                "admin_ipcheck_item",
                flag=icon,
                name=html.escape(name),
                target=html.escape(target),
                status=status,
            )
        )

    today = datetime.now(UTC).date()
    usage = await panel_service.get_nodes_bandwidth_usage(
        start=today.replace(day=1).isoformat(),
        end=today.isoformat(),
    )
    lines.append("")
    lines.append(f"<b>{_('admin_ipcheck_traffic_header')}</b>")
    if usage is None:
        lines.append(_("admin_ipcheck_traffic_unavailable"))
    else:
        watched = set(watched_node_uuids(settings))
        lte_total = 0
        for node in usage.get("topNodes") or []:
            total = int(node.get("total") or 0)
            is_lte = str(node.get("uuid") or "") in watched
            if is_lte:
                lte_total += total
            lines.append(
                _(
                    "admin_ipcheck_traffic_item",
                    flag=_node_flag(
                        str(node.get("name") or ""),
                        str(node.get("countryCode") or ""),
                        flag_by_id,
                    ),
                    name=html.escape(str(node.get("name") or "?")),
                    gb=f"{total / (1024**3):.1f}",
                    lte=" 📱" if is_lte else "",
                )
            )
        lines.append(
            _("admin_ipcheck_traffic_total", gb=f"{lte_total / (1024**3):.1f}")
        )

    await progress.edit_text("\n".join(lines))
