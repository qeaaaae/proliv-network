import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from bot.infra.promo_policies import (
    PromoCheckoutSuggestionContext,
    resolve_promo_checkout_suggestions,
)
from bot.services import referral_checkout_promo as rcp


def _ctx(user_id: int = 42, sale_mode_base: str | None = "subscription"):
    return PromoCheckoutSuggestionContext(
        session=object(),
        user_id=user_id,
        sale_mode_base=sale_mode_base,
    )


def _settings(*, enabled: bool = True, discount: float = 10.0):
    return SimpleNamespace(
        referral_settings=SimpleNamespace(enabled=enabled),
        REFERRAL_PROGRAM_ENABLED=enabled,
        REFERRAL_FRIEND_DISCOUNT_PERCENT=discount,
    )


def _promo(**overrides):
    base = {
        "code": "RF42",
        "is_active": True,
        "archived_at": None,
        "current_activations": 0,
        "max_activations": 1,
    }
    return SimpleNamespace(**{**base, **overrides})


def _patch_user(monkeypatch, referred_by_id):
    monkeypatch.setattr(
        rcp.user_dal,
        "get_user_by_id",
        AsyncMock(return_value=SimpleNamespace(user_id=42, referred_by_id=referred_by_id)),
    )


def test_suggests_personal_code_for_invited_user(monkeypatch):
    monkeypatch.setattr(rcp, "get_settings", lambda: _settings())
    _patch_user(monkeypatch, referred_by_id=7)
    mint = AsyncMock(return_value=_promo())
    monkeypatch.setattr(rcp, "ensure_referral_friend_promo", mint)

    result = asyncio.run(rcp.referral_friend_promo_suggestion(_ctx()))

    assert result == "RF42"
    mint.assert_awaited_once()
    kwargs = mint.await_args.kwargs
    assert kwargs["user_id"] == 42
    assert kwargs["discount_percent"] == 10.0


def test_no_suggestion_without_referrer(monkeypatch):
    monkeypatch.setattr(rcp, "get_settings", lambda: _settings())
    _patch_user(monkeypatch, referred_by_id=None)
    mint = AsyncMock(return_value=_promo())
    monkeypatch.setattr(rcp, "ensure_referral_friend_promo", mint)

    assert asyncio.run(rcp.referral_friend_promo_suggestion(_ctx())) is None
    mint.assert_not_called()


def test_no_suggestion_for_missing_user(monkeypatch):
    monkeypatch.setattr(rcp, "get_settings", lambda: _settings())
    monkeypatch.setattr(rcp.user_dal, "get_user_by_id", AsyncMock(return_value=None))

    assert asyncio.run(rcp.referral_friend_promo_suggestion(_ctx())) is None


@pytest.mark.parametrize("sale_mode_base", ["topup", "trial", "premium_topup"])
def test_no_suggestion_outside_subscription_scope(monkeypatch, sale_mode_base):
    monkeypatch.setattr(rcp, "get_settings", lambda: _settings())
    get_user = AsyncMock(return_value=None)
    monkeypatch.setattr(rcp.user_dal, "get_user_by_id", get_user)

    result = asyncio.run(rcp.referral_friend_promo_suggestion(_ctx(sale_mode_base=sale_mode_base)))

    assert result is None
    get_user.assert_not_called()


def test_no_suggestion_when_referral_program_disabled(monkeypatch):
    monkeypatch.setattr(rcp, "get_settings", lambda: _settings(enabled=False))
    _patch_user(monkeypatch, referred_by_id=7)
    mint = AsyncMock(return_value=_promo())
    monkeypatch.setattr(rcp, "ensure_referral_friend_promo", mint)

    assert asyncio.run(rcp.referral_friend_promo_suggestion(_ctx())) is None
    mint.assert_not_called()


def test_no_suggestion_when_discount_disabled(monkeypatch):
    monkeypatch.setattr(rcp, "get_settings", lambda: _settings(discount=0))
    _patch_user(monkeypatch, referred_by_id=7)
    mint = AsyncMock(return_value=_promo())
    monkeypatch.setattr(rcp, "ensure_referral_friend_promo", mint)

    assert asyncio.run(rcp.referral_friend_promo_suggestion(_ctx())) is None
    mint.assert_not_called()


def test_exhausted_or_inactive_promo_not_suggested(monkeypatch):
    monkeypatch.setattr(rcp, "get_settings", lambda: _settings())
    _patch_user(monkeypatch, referred_by_id=7)
    mint = AsyncMock(return_value=_promo(current_activations=1))
    monkeypatch.setattr(rcp, "ensure_referral_friend_promo", mint)

    assert asyncio.run(rcp.referral_friend_promo_suggestion(_ctx())) is None


def test_mint_creates_single_use_personal_discount(monkeypatch):
    session = AsyncMock()
    monkeypatch.setattr(rcp.promo_code_dal, "get_promo_code_by_code", AsyncMock(return_value=None))
    created = _promo()
    create = AsyncMock(return_value=created)
    monkeypatch.setattr(rcp.promo_code_dal, "create_promo_code", create)

    promo = asyncio.run(rcp._mint_referral_friend_promo(session, user_id=42, discount_percent=10.0))

    assert promo is created
    promo_data = create.await_args.args[1]
    assert promo_data["code"] == "RF42"
    assert promo_data["discount_percent"] == 10.0
    assert promo_data["applies_to"] == "subscription"
    assert promo_data["user_id"] == 42
    assert promo_data["max_activations"] == 1
    assert promo_data["bonus_days"] == 0
    session.commit.assert_awaited_once()


def test_mint_returns_existing_code_without_creating(monkeypatch):
    session = AsyncMock()
    existing = _promo()
    monkeypatch.setattr(
        rcp.promo_code_dal,
        "get_promo_code_by_code",
        AsyncMock(return_value=existing),
    )
    create = AsyncMock()
    monkeypatch.setattr(rcp.promo_code_dal, "create_promo_code", create)

    promo = asyncio.run(rcp._mint_referral_friend_promo(session, user_id=42, discount_percent=10.0))

    assert promo is existing
    create.assert_not_called()
    session.commit.assert_not_called()


def test_core_provider_participates_in_resolver(monkeypatch):
    monkeypatch.setattr(rcp, "get_settings", lambda: _settings())
    _patch_user(monkeypatch, referred_by_id=7)
    monkeypatch.setattr(rcp, "ensure_referral_friend_promo", AsyncMock(return_value=_promo()))

    result = asyncio.run(resolve_promo_checkout_suggestions(_ctx()))

    assert result == ("RF42",)
