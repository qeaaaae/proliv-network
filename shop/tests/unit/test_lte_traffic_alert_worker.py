from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any, cast
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

import main_worker

from bot.services import lte_traffic_alert_worker as worker_module
from bot.services.lte_traffic_alert_worker import (
    LTE_TRAFFIC_ALERT_EVENT,
    LteTrafficAlertWorker,
    collect_usage_totals,
    watched_node_uuids,
)

_GB = 1024**3


class _SessionContext:
    def __init__(self, session: AsyncMock) -> None:
        self.session = session

    async def __aenter__(self) -> AsyncMock:
        return self.session

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False


class _SessionFactory:
    def __init__(self) -> None:
        self.sessions: list[AsyncMock] = []

    def __call__(self) -> _SessionContext:
        session = AsyncMock()
        self.sessions.append(session)
        return _SessionContext(session)


def _settings(**overrides: Any) -> SimpleNamespace:
    base: dict[str, Any] = {
        "LTE_TRAFFIC_ALERT_ENABLED": True,
        "LTE_TRAFFIC_ALERT_GB_PER_DAY": 20.0,
        "LTE_TRAFFIC_ALERT_NODE_UUIDS": "node-1 , node-2,node-1",
        "LTE_TRAFFIC_ALERT_TICK_SECONDS": 3600,
        "DEFAULT_LANGUAGE": "ru",
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def _payload(*entries: dict[str, Any]) -> dict[str, Any]:
    return {"nodes": [{"uuid": "node-1", "users": list(entries)}]}


class CollectUsageTotalsTests(IsolatedAsyncioTestCase):
    def test_aggregates_v3_entries_across_nodes(self) -> None:
        payload = {
            "nodes": [
                {
                    "uuid": "node-1",
                    "users": [
                        {"id": "u-1", "totalBytes": 5},
                        {"id": "u-1", "total": 7},
                        {"id": "u-2", "download": 3, "upload": 4},
                    ],
                },
                {
                    "uuid": "node-2",
                    "users": [
                        {"user": {"uuid": "u-1", "username": "alice"}, "total": 11},
                        {"userUuid": "u-3", "userUsername": "bob", "total": 2},
                    ],
                },
            ]
        }
        totals = collect_usage_totals(payload)
        self.assertEqual(totals["u-1"]["bytes"], 23)
        self.assertEqual(totals["u-2"]["bytes"], 7)
        self.assertEqual(totals["u-3"]["bytes"], 2)

    def test_ignores_malformed_payload(self) -> None:
        self.assertEqual(collect_usage_totals(None), {})
        self.assertEqual(collect_usage_totals({"nodes": "nope"}), {})
        self.assertEqual(collect_usage_totals({"nodes": [{"users": [{"total": 1}]}]}), {})


class WatchedNodeUuidsTests(IsolatedAsyncioTestCase):
    def test_parses_csv_and_dedupes(self) -> None:
        self.assertEqual(
            watched_node_uuids(cast(Any, _settings())),
            ["node-1", "node-2"],
        )

    def test_empty_disables(self) -> None:
        self.assertEqual(
            watched_node_uuids(
                cast(Any, _settings(LTE_TRAFFIC_ALERT_NODE_UUIDS="  "))
            ),
            [],
        )


class LteTrafficAlertWorkerTests(IsolatedAsyncioTestCase):
    def _worker(
        self,
        *,
        payload: dict[str, Any] | None,
        settings: SimpleNamespace | None = None,
    ) -> tuple[LteTrafficAlertWorker, Any, Any, _SessionFactory]:
        panel_service = SimpleNamespace(
            get_multi_node_user_usage=AsyncMock(return_value=payload)
        )
        notification_service = SimpleNamespace(
            send_custom_notification=AsyncMock()
        )
        session_factory = _SessionFactory()
        worker = LteTrafficAlertWorker(
            cast(Any, settings or _settings()),
            cast(Any, session_factory),
            cast(Any, panel_service),
            cast(Any, notification_service),
            None,
        )
        return worker, panel_service, notification_service, session_factory

    async def test_disabled_or_unconfigured_skips_panel_call(self) -> None:
        worker, panel_service, _, _ = self._worker(
            payload=None,
            settings=_settings(LTE_TRAFFIC_ALERT_NODE_UUIDS=""),
        )
        self.assertEqual(await worker.tick(), 0)
        panel_service.get_multi_node_user_usage.assert_not_awaited()

        worker, panel_service, _, _ = self._worker(
            payload=None,
            settings=_settings(LTE_TRAFFIC_ALERT_ENABLED=False),
        )
        self.assertEqual(await worker.tick(), 0)
        panel_service.get_multi_node_user_usage.assert_not_awaited()

    async def test_heavy_user_alerts_admins_and_log_channel(self) -> None:
        used = int(25 * _GB)
        worker, panel_service, notifications, session_factory = self._worker(
            payload=_payload({"id": "u-1", "totalBytes": used})
        )
        user = SimpleNamespace(
            user_id=1001,
            username="heavy",
            first_name="Heavy",
            last_name=None,
            telegram_id=555,
        )
        today = datetime.now(UTC).date().isoformat()
        with (
            patch.object(
                worker_module.message_log_dal,
                "has_event_content",
                AsyncMock(return_value=False),
            ) as has_content,
            patch.object(
                worker_module.user_dal,
                "get_user_by_panel_uuid",
                AsyncMock(return_value=user),
            ),
            patch.object(
                worker_module,
                "log_user_message_delivery",
                AsyncMock(),
            ) as audit,
        ):
            sent = await worker.tick()

        self.assertEqual(sent, 1)
        panel_service.get_multi_node_user_usage.assert_awaited_once()
        call = panel_service.get_multi_node_user_usage.await_args
        self.assertEqual(call.args[0], ["node-1", "node-2"])
        self.assertEqual(call.kwargs["start"], today)
        self.assertEqual(call.kwargs["end"], today)
        notifications.send_custom_notification.assert_awaited_once()
        notify_kwargs = notifications.send_custom_notification.await_args.kwargs
        self.assertTrue(notify_kwargs["to_admins"])
        self.assertTrue(notify_kwargs["to_log_channel"])
        message = notifications.send_custom_notification.await_args.args[0]
        self.assertIn("Heavy", message)
        self.assertIn("25.0", message)
        has_content.assert_awaited_once()
        self.assertEqual(
            has_content.await_args.kwargs["content_fragment"],
            f"fingerprint={today}:u-1:1",
        )
        audit.assert_awaited_once()
        self.assertEqual(
            audit.await_args.kwargs["event_type"], LTE_TRAFFIC_ALERT_EVENT
        )
        self.assertEqual(audit.await_args.kwargs["target_user_id"], 1001)
        session_factory.sessions[0].commit.assert_awaited_once()

    async def test_under_threshold_does_not_alert(self) -> None:
        worker, _, notifications, _ = self._worker(
            payload=_payload({"id": "u-1", "totalBytes": int(19 * _GB)})
        )
        with patch.object(
            worker_module.message_log_dal,
            "has_event_content",
            AsyncMock(return_value=False),
        ) as has_content:
            sent = await worker.tick()
        self.assertEqual(sent, 0)
        notifications.send_custom_notification.assert_not_awaited()
        has_content.assert_not_awaited()

    async def test_deduped_fingerprint_skips_alert(self) -> None:
        worker, _, notifications, _ = self._worker(
            payload=_payload({"id": "u-1", "totalBytes": int(25 * _GB)})
        )
        with patch.object(
            worker_module.message_log_dal,
            "has_event_content",
            AsyncMock(return_value=True),
        ):
            sent = await worker.tick()
        self.assertEqual(sent, 0)
        notifications.send_custom_notification.assert_not_awaited()

    async def test_second_threshold_multiple_fires_new_fingerprint(self) -> None:
        today = datetime.now(UTC).date().isoformat()
        worker, _, notifications, _ = self._worker(
            payload=_payload({"id": "u-1", "totalBytes": int(45 * _GB)})
        )
        fragments: list[str] = []

        async def _record(*_args: Any, **kwargs: Any) -> bool:
            fragments.append(str(kwargs.get("content_fragment")))
            return False

        with (
            patch.object(
                worker_module.message_log_dal,
                "has_event_content",
                AsyncMock(side_effect=_record),
            ),
            patch.object(
                worker_module.user_dal,
                "get_user_by_panel_uuid",
                AsyncMock(return_value=None),
            ),
            patch.object(
                worker_module.user_dal,
                "get_user_by_username",
                AsyncMock(return_value=None),
            ),
            patch.object(
                worker_module,
                "log_user_message_delivery",
                AsyncMock(),
            ) as audit,
        ):
            sent = await worker.tick()
        self.assertEqual(sent, 1)
        self.assertEqual(fragments, [f"fingerprint={today}:u-1:2"])
        self.assertIsNone(audit.await_args.kwargs["target_user_id"])
        notifications.send_custom_notification.assert_awaited_once()


def test_core_worker_registers_lte_traffic_alert() -> None:
    assert "LteTrafficAlertWorker" in {
        task.name for task in main_worker._core_worker_tasks()
    }
