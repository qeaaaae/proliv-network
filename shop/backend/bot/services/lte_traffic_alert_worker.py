"""Admin alerts for heavy per-user traffic on watched (e.g. LTE) panel nodes."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import time
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from aiogram.utils.text_decorations import html_decoration as hd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from bot.infra.redis import redis_lock
from bot.middlewares.i18n import JsonI18n
from bot.services.message_audit import log_user_message_delivery
from config.settings import Settings
from db.dal import message_log_dal, user_dal
from db.models import User

if TYPE_CHECKING:
    from bot.services.notification_service import NotificationService
    from bot.services.panel_api_service import PanelApiService

logger = logging.getLogger(__name__)

LTE_TRAFFIC_ALERT_LOCK = "lte-traffic-alert"
LTE_TRAFFIC_ALERT_EVENT = "admin_lte_traffic_alert"
_BYTES_PER_GB = 1024**3


def watched_node_uuids(settings: Settings) -> list[str]:
    raw = str(getattr(settings, "LTE_TRAFFIC_ALERT_NODE_UUIDS", "") or "")
    return list(dict.fromkeys(part.strip() for part in raw.split(",") if part.strip()))


def _entry_total_bytes(entry: dict[str, Any]) -> int:
    raw_total = (
        entry.get("totalBytes") if entry.get("totalBytes") is not None else entry.get("total")
    )
    if raw_total is None:
        raw_total = int(entry.get("download", 0) or 0) + int(entry.get("upload", 0) or 0)
    try:
        return max(0, int(raw_total or 0))
    except (TypeError, ValueError):
        return 0


def collect_usage_totals(payload: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    """Aggregate per-user byte totals across nodes in a multi-node usage response."""
    result: dict[str, dict[str, Any]] = {}
    if not isinstance(payload, dict):
        return result
    nodes = payload.get("nodes")
    if not isinstance(nodes, list):
        return result
    for node in nodes:
        if not isinstance(node, dict):
            continue
        users = node.get("users")
        if not isinstance(users, list):
            continue
        for entry in users:
            if not isinstance(entry, dict):
                continue
            user_obj_raw = entry.get("user")
            user_obj: dict[str, Any] = user_obj_raw if isinstance(user_obj_raw, dict) else {}
            entry_uuid = (
                user_obj.get("uuid")
                or entry.get("userUuid")
                or entry.get("uuid")
                or entry.get("user_uuid")
                or entry.get("id")
                or entry.get("userId")
            )
            entry_username = (
                user_obj.get("username") or entry.get("username") or entry.get("userUsername")
            )
            key = str(entry_uuid or entry_username or "").strip()
            if not key:
                continue
            slot = result.setdefault(
                key, {"uuid": entry_uuid, "username": entry_username, "bytes": 0}
            )
            slot["bytes"] += _entry_total_bytes(entry)
    return result


def _user_display(user: User | None, *, panel_key: str) -> str:
    if user is None:
        return f"panel {hd.quote(panel_key)}"
    full_name = " ".join(
        part for part in (str(user.first_name or ""), str(user.last_name or "")) if part
    ).strip()
    if full_name:
        label = hd.quote(full_name)
    elif user.username:
        label = f"@{hd.quote(str(user.username))}"
    else:
        label = f"user #{user.user_id}"
    extras: list[str] = []
    if user.username and full_name:
        extras.append(f"@{hd.quote(str(user.username))}")
    if user.telegram_id:
        extras.append(f"tg {user.telegram_id}")
    extras.append(f"user #{user.user_id}")
    return f"{label} ({', '.join(extras)})"


class LteTrafficAlertWorker:
    def __init__(
        self,
        settings: Settings,
        session_factory: sessionmaker,
        panel_service: PanelApiService,
        notification_service: NotificationService | None,
        i18n: JsonI18n | None,
    ) -> None:
        self.settings = settings
        self.session_factory = session_factory
        self.panel_service = panel_service
        self.notification_service = notification_service
        self.i18n = i18n
        self._stopped = asyncio.Event()
        self._no_nodes_logged = False

    async def run(self) -> None:
        while not self._stopped.is_set():
            tick_seconds = max(
                60,
                int(getattr(self.settings, "LTE_TRAFFIC_ALERT_TICK_SECONDS", 3600) or 3600),
            )
            try:
                async with redis_lock(
                    self.settings,
                    LTE_TRAFFIC_ALERT_LOCK,
                    ttl_seconds=tick_seconds,
                ) as acquired:
                    if acquired:
                        started = time.monotonic()
                        sent = await self.tick()
                        logger.info(
                            "metric worker_tick_duration_seconds=%.3f "
                            "worker=lte_traffic_alert alerts=%s",
                            time.monotonic() - started,
                            sent,
                        )
            except Exception:
                logger.exception("LTE traffic alert worker tick failed")
            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(self._stopped.wait(), timeout=tick_seconds)

    def stop(self) -> None:
        self._stopped.set()

    async def tick(self) -> int:
        if not getattr(self.settings, "LTE_TRAFFIC_ALERT_ENABLED", True):
            return 0
        node_uuids = watched_node_uuids(self.settings)
        if not node_uuids:
            if not self._no_nodes_logged:
                logger.info("LTE traffic alert skipped: no watched node UUIDs configured")
                self._no_nodes_logged = True
            return 0
        self._no_nodes_logged = False
        threshold_gb = float(
            getattr(self.settings, "LTE_TRAFFIC_ALERT_GB_PER_DAY", 20.0) or 0
        )
        threshold_bytes = int(threshold_gb * _BYTES_PER_GB)
        if threshold_bytes <= 0:
            return 0
        today = datetime.now(UTC).date().isoformat()
        payload = await self.panel_service.get_multi_node_user_usage(
            node_uuids,
            start=today,
            end=today,
            min_total_bytes=threshold_bytes,
        )
        if payload is None:
            logger.warning("LTE traffic alert: panel usage stats unavailable")
            return 0
        totals = collect_usage_totals(payload)
        sent = 0
        async with self.session_factory() as session:
            for panel_key, entry in sorted(
                totals.items(),
                key=lambda item: int(item[1]["bytes"]),
                reverse=True,
            ):
                if int(entry["bytes"]) < threshold_bytes:
                    continue
                if await self._maybe_alert(
                    session,
                    panel_key=panel_key,
                    entry=entry,
                    today=today,
                    threshold_gb=threshold_gb,
                    threshold_bytes=threshold_bytes,
                ):
                    sent += 1
            await session.commit()
        return sent

    async def _maybe_alert(
        self,
        session: AsyncSession,
        *,
        panel_key: str,
        entry: dict[str, Any],
        today: str,
        threshold_gb: float,
        threshold_bytes: int,
    ) -> bool:
        used_bytes = int(entry["bytes"])
        # Alert once per multiple of the threshold: 20 GB fires, then again at 40 GB, ...
        bucket = int(used_bytes // threshold_bytes)
        fingerprint = f"{today}:{panel_key}:{bucket}"
        if await message_log_dal.has_event_content(
            session,
            event_type=LTE_TRAFFIC_ALERT_EVENT,
            content_fragment=f"fingerprint={fingerprint}",
        ):
            return False
        user = await self._resolve_user(session, entry)
        message = self._alert_text(
            user=user,
            panel_key=panel_key,
            used_bytes=used_bytes,
            threshold_gb=threshold_gb,
        )
        if self.notification_service is not None:
            await self.notification_service.send_custom_notification(
                message,
                to_admins=True,
                to_log_channel=True,
            )
        else:
            logger.warning(
                "LTE traffic alert (notification service unavailable): %s", message
            )
        await log_user_message_delivery(
            session,
            target_user_id=int(user.user_id) if user is not None else None,
            event_type=LTE_TRAFFIC_ALERT_EVENT,
            channel="admin_alert",
            content=f"fingerprint={fingerprint} bytes={used_bytes}",
        )
        return True

    async def _resolve_user(
        self,
        session: AsyncSession,
        entry: dict[str, Any],
    ) -> User | None:
        panel_uuid = str(entry.get("uuid") or "").strip()
        if panel_uuid:
            user = await user_dal.get_user_by_panel_uuid(session, panel_uuid)
            if user is not None:
                return user
        username = str(entry.get("username") or "").strip()
        if username:
            return await user_dal.get_user_by_username(session, username)
        return None

    def _alert_text(
        self,
        *,
        user: User | None,
        panel_key: str,
        used_bytes: int,
        threshold_gb: float,
    ) -> str:
        used_gb = used_bytes / _BYTES_PER_GB
        display = _user_display(user, panel_key=panel_key)
        timestamp = datetime.now(UTC).strftime("%d.%m.%Y %H:%M")
        if self.i18n is not None:
            text = self.i18n.gettext(
                self.settings.DEFAULT_LANGUAGE,
                "admin_lte_traffic_alert",
                user_display=display,
                gb_used=f"{used_gb:.1f}",
                threshold_gb=f"{threshold_gb:g}",
                timestamp=timestamp,
            )
            if text and text != "admin_lte_traffic_alert":
                return text
        return (
            "🚀 <b>LTE heavy traffic alert</b>\n\n"
            f"{display}\n"
            f"📊 Today: <b>{used_gb:.1f} GB</b> (threshold {threshold_gb:g} GB)\n"
            f"🕐 {timestamp}"
        )
