from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

from bot.services.partner_commission_service import PartnerCommissionService
from bot.services.partner_common import streamer_commission_bps
from config.settings_models import PartnerSettings
from db.dal import partner_dal


def test_streamer_commission_bps_table() -> None:
    config = PartnerSettings()
    assert (
        streamer_commission_bps(
            config, banner_below_stream=True, banner_on_stream=True
        )
        == config.streamer_rate_both_bps
    )
    assert (
        streamer_commission_bps(
            config, banner_below_stream=True, banner_on_stream=False
        )
        == config.streamer_rate_below_bps
    )
    assert (
        streamer_commission_bps(
            config, banner_below_stream=False, banner_on_stream=True
        )
        == config.streamer_rate_on_bps
    )
    assert (
        streamer_commission_bps(
            config, banner_below_stream=False, banner_on_stream=False
        )
        == config.default_commission_bps
    )


def _service() -> PartnerCommissionService:
    return PartnerCommissionService(
        SimpleNamespace(partner_settings=PartnerSettings())
    )


def _session() -> SimpleNamespace:
    return SimpleNamespace(flush=AsyncMock())


def test_update_kind_flags_streamer_recomputes_rate(monkeypatch) -> None:
    profile = SimpleNamespace(
        partner_id=7,
        kind="standard",
        banner_below_stream=False,
        banner_on_stream=False,
        commission_bps=1500,
        updated_at=None,
    )
    audit = AsyncMock()
    monkeypatch.setattr(
        partner_dal, "get_profile_by_id", AsyncMock(return_value=profile)
    )
    monkeypatch.setattr(partner_dal, "create_audit_event", audit)

    result = asyncio.run(
        _service().update_kind_flags(
        _session(),
        partner_id=7,
        kind="streamer",
        banner_below_stream=True,
        banner_on_stream=True,
            actor_admin_id=1,
        )
    )
    assert result.kind == "streamer"
    assert result.banner_below_stream is True
    assert result.banner_on_stream is True
    assert result.commission_bps == 6000
    audit.assert_awaited_once()


def test_update_kind_flags_clipper_clears_placements_and_rate(
    monkeypatch,
) -> None:
    profile = SimpleNamespace(
        partner_id=7,
        kind="streamer",
        banner_below_stream=True,
        banner_on_stream=True,
        commission_bps=6000,
        updated_at=None,
    )
    monkeypatch.setattr(
        partner_dal, "get_profile_by_id", AsyncMock(return_value=profile)
    )
    monkeypatch.setattr(partner_dal, "create_audit_event", AsyncMock())

    result = asyncio.run(
        _service().update_kind_flags(
        _session(),
        partner_id=7,
        kind="clipper",
            actor_admin_id=1,
        )
    )
    assert result.kind == "clipper"
    assert result.banner_below_stream is False
    assert result.banner_on_stream is False
    assert result.commission_bps == 0


def test_update_kind_flags_standard_keeps_rate(monkeypatch) -> None:
    profile = SimpleNamespace(
        partner_id=7,
        kind="streamer",
        banner_below_stream=False,
        banner_on_stream=True,
        commission_bps=5000,
        updated_at=None,
    )
    monkeypatch.setattr(
        partner_dal, "get_profile_by_id", AsyncMock(return_value=profile)
    )
    monkeypatch.setattr(partner_dal, "create_audit_event", AsyncMock())

    result = asyncio.run(
        _service().update_kind_flags(
        _session(),
        partner_id=7,
        kind="standard",
            actor_admin_id=1,
        )
    )
    assert result.kind == "standard"
    assert result.banner_below_stream is False
    assert result.banner_on_stream is False
    assert result.commission_bps == 5000
