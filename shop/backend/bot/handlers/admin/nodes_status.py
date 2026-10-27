import asyncio
import json
import logging
import time
from pathlib import Path

from aiogram import Router, types
from aiogram.filters import Command

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

    lines = [f"<b>{_('admin_nodes_header')}</b>"]
    for loc in data.get("groups", {}).get("locations", []):
        icon = "🟢" if loc.get("up") else "🔴"
        stats = loc.get("stats") or {}
        if stats:
            lines.append(
                _(
                    "admin_nodes_item",
                    icon=icon,
                    name=loc.get("name", "?"),
                    load=stats.get("load1", "-"),
                    mem=stats.get("mem_used_mb", "-"),
                    mem_total=stats.get("mem_total_mb", "-"),
                    disk=stats.get("disk_pct", "-"),
                    conns=stats.get("conns", "-"),
                    uptime=loc.get("uptime", "-"),
                )
            )
        else:
            lines.append(
                _(
                    "admin_nodes_item_nostats",
                    icon=icon,
                    name=loc.get("name", "?"),
                    state=loc.get("state", "?"),
                )
            )
    for svc in data.get("groups", {}).get("services", []):
        icon = "🟢" if svc.get("up") else "🔴"
        lines.append(
            _(
                "admin_nodes_service_item",
                icon=icon,
                name=svc.get("name", "?"),
                state=svc.get("state", "?"),
            )
        )

    updated = data.get("updated_at")
    if updated:
        stamp = time.strftime("%d.%m %H:%M", time.gmtime(updated))
        lines.append(f"<i>{_('admin_nodes_updated')}: {stamp}</i>")

    await message.answer("\n".join(lines), parse_mode="HTML")
