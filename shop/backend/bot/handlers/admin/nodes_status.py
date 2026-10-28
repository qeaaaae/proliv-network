import asyncio
import html
import json
import logging
import time
from pathlib import Path

from aiogram import Router, types
from aiogram.filters import Command

from bot.handlers.admin.nodes_geo import flag, render_location_block
from bot.middlewares.i18n import JsonI18n
from config.settings import Settings

logger = logging.getLogger(__name__)

router = Router(name="admin_nodes_status_router")

STATUS_FILE = Path("/status/status.json")


@router.message(Command("nodes"))
async def nodes_status_command_handler(
    message: types.Message, settings: Settings, i18n_data: dict
) -> None:
    current_lang = i18n_data.get("current_language", settings.DEFAULT_LANGUAGE)
    i18n: JsonI18n | None = i18n_data.get("i18n_instance")
    if not i18n:
        await message.answer("Language service error.")
        return
    _ = lambda key, **kwargs: i18n.gettext(current_lang, key, **kwargs)

    try:
        raw = await asyncio.to_thread(STATUS_FILE.read_text, encoding="utf-8")
        data = json.loads(raw)
    except (OSError, ValueError) as exc:
        logger.warning("nodes status: cannot read %s: %s", STATUS_FILE, exc)
        await message.answer(_("admin_nodes_unavailable"))
        return

    blocks = [f"<b>{_('admin_nodes_header')}</b>"]
    for loc in data.get("groups", {}).get("locations", []):
        icon = "🟢" if loc.get("up") else "🔴"
        country = str(loc.get("flag") or "").upper()
        name = html.escape(str(loc.get("name", "?")))
        header = f"{icon} {flag(country)} <b>{name}</b>" + (f" · {country}" if country else "")
        stats = loc.get("stats") or {}
        if stats:
            detail = _(
                "admin_nodes_item",
                load=stats.get("load1", "-"),
                mem=stats.get("mem_used_mb", "-"),
                mem_total=stats.get("mem_total_mb", "-"),
                disk=stats.get("disk_pct", "-"),
                conns=stats.get("conns", "-"),
                uptime=loc.get("uptime", "-"),
            )
        else:
            detail = _("admin_nodes_item_nostats", state=loc.get("state", "?"))
        geo = loc.get("geo")
        blocks.append(
            render_location_block(
                header, [detail], country, geo if isinstance(geo, dict) else None, _
            )
        )

    services = [
        _(
            "admin_nodes_service_item",
            icon="🟢" if svc.get("up") else "🔴",
            name=svc.get("name", "?"),
            state=svc.get("state", "?"),
        )
        for svc in data.get("groups", {}).get("services", [])
    ]
    if services:
        blocks.append("\n".join(services))

    updated = data.get("updated_at")
    if updated:
        stamp = time.strftime("%d.%m %H:%M", time.gmtime(updated))
        blocks.append(f"<i>{_('admin_nodes_updated')}: {stamp}</i>")

    await message.answer("\n\n".join(blocks), parse_mode="HTML", disable_web_page_preview=True)
