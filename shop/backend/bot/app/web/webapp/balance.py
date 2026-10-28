from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from aiohttp import web

from bot.app.web.context import (
    get_session_factory,
    get_settings,
    get_subscription_service,
)
from bot.services.partner_common import amount_to_minor, currency_scale
from bot.services.user_balance_service import UserBalanceService
from db.dal import user_balance_dal, user_dal

from .assets import _enforce_webapp_rate_limit
from .billing_payments import _create_subscription_payment
from .common import (
    _invalidate_webapp_user_caches,
    _json_error,
    _normalize_language,
    _parse_model_payload,
    _require_user_id,
)
from .payloads import WebAppBalanceTopupPayload, WebAppReferralExchangePayload
from .response_helpers import json_response
from .serializers import _webapp_datetime_text

logger = logging.getLogger(__name__)


async def balance_route(request: web.Request) -> web.Response:
    user_id = _require_user_id(request)
    settings = get_settings(request)
    async with get_session_factory(request)() as session:
        payload = await UserBalanceService(settings).snapshot(
            session,
            user_id=user_id,
            include_history=False,
        )
    return json_response({"ok": True, **payload})


async def balance_topup_route(request: web.Request) -> web.Response:
    user_id = _require_user_id(request)
    limited = await _enforce_webapp_rate_limit(
        request,
        user_id=user_id,
        action="balance-topup",
    )
    if limited is not None:
        return limited
    settings = get_settings(request)
    config = settings.balance_settings
    if not config.enabled:
        return _json_error(403, "user_balance_disabled", "User balance is disabled")
    payload = await _parse_model_payload(request, WebAppBalanceTopupPayload)
    amount = float(payload.amount)
    minor_amount = Decimal(str(amount)) * 10 ** currency_scale(config.currency)
    if minor_amount != minor_amount.to_integral_value():
        return _json_error(400, "balance_topup_invalid_precision", "Invalid amount precision")
    if amount < config.topup_min_amount:
        return _json_error(400, "balance_topup_below_minimum", "Top-up amount is too small")
    if amount > config.topup_max_amount:
        return _json_error(400, "balance_topup_above_maximum", "Top-up amount is too large")
    method = payload.method.strip().lower()
    if method in {"", "stars", "partner_balance", "user_balance"}:
        return _json_error(
            400,
            "balance_topup_payment_unavailable",
            "This payment method cannot top up a balance",
        )
    async with get_session_factory(request)() as session:
        user = await user_dal.get_user_by_id(session, user_id)
        if user is None or bool(user.is_banned):
            return _json_error(403, "access_denied", "Access denied")
        from bot.services.account_roles import is_admin as account_is_admin

        is_admin = await account_is_admin(session, user_id)
        logger.info(
            "Balance top-up requested: user_id=%s amount=%s currency=%s provider=%s",
            user_id,
            amount,
            config.currency,
            method,
        )
        return await _create_subscription_payment(
            request=request,
            session=session,
            user_id=user_id,
            method=method,
            months=1,
            price=amount,
            stars_price=None,
            currency=config.currency,
            lang=_normalize_language(user.language_code or settings.DEFAULT_LANGUAGE),
            sale_mode="balance_topup",
            is_admin=is_admin,
        )


async def referral_exchange_route(request: web.Request) -> web.Response:
    user_id = _require_user_id(request)
    limited = await _enforce_webapp_rate_limit(
        request,
        user_id=user_id,
        action="referral-exchange",
    )
    if limited is not None:
        return limited
    settings = get_settings(request)
    payload = await _parse_model_payload(request, WebAppReferralExchangePayload)
    days = int(payload.days)

    price = settings.BONUS_EXCHANGE_DAY_PRICE
    currency = settings.balance_settings.currency
    scale = currency_scale(currency)
    price_minor = amount_to_minor(price, scale=scale) if price and price > 0 else 0
    if price_minor <= 0:
        return _json_error(400, "bonus_exchange_unavailable", "Bonus exchange is not available")

    subscription_service = get_subscription_service(request)
    async with get_session_factory(request)() as session:
        user = await user_dal.get_user_by_id(session, user_id)
        if user is None or bool(user.is_banned):
            await session.rollback()
            return _json_error(403, "access_denied", "Access denied")
        await user_dal.lock_user_by_id(session, user_id)

        balance_minor = await user_balance_dal.balance_minor(session, user_id, currency)
        if days > int(balance_minor // price_minor):
            await session.rollback()
            return _json_error(400, "bonus_exchange_insufficient", "Not enough bonus balance")

        spend_minor = days * price_minor
        exchange_id = uuid4().hex
        await user_balance_dal.create_ledger_entry(
            session,
            user_id=user_id,
            currency=currency,
            currency_scale=scale,
            amount_minor=-spend_minor,
            kind="extension_purchase",
            state="posted",
            reference_type="bonus_exchange",
            reference_id=f"bonus-exchange:{user_id}:{exchange_id[:16]}",
            idempotency_key=f"bonus-exchange:{exchange_id}",
            reason="bonus balance exchange to subscription days",
            posted_at=datetime.now(UTC),
        )
        try:
            new_end_date = await subscription_service.extend_active_subscription_days(
                session,
                user_id=user_id,
                bonus_days=days,
                reason="bonus exchange",
            )
        except Exception:
            await session.rollback()
            logger.exception("Webapp bonus exchange failed while extending user %s.", user_id)
            return _json_error(500, "bonus_exchange_failed", "Bonus exchange failed")
        if not new_end_date:
            await session.rollback()
            return _json_error(
                400, "bonus_exchange_unavailable", "No active subscription to extend"
            )
        await session.commit()

    await _invalidate_webapp_user_caches(settings, user_id, include_devices=True)
    return json_response(
        {
            "ok": True,
            "days": days,
            "end_date": new_end_date.isoformat() if isinstance(new_end_date, datetime) else None,
            "end_date_text": _webapp_datetime_text(new_end_date),
        }
    )
