"""Retire a user's older unpaid invoices that carry the same promo code.

Checkout promo redemption no longer refuses a replacement invoice just
because an older pending invoice already holds the code. Once the new
payment record exists, the older hosted checkout is canceled at the
provider and finalized as ``superseded_checkout``, so a single-use promo
slot cannot be consumed twice.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from types import SimpleNamespace
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from db.dal import payment_checkout_dal, payment_dal

logger = logging.getLogger(__name__)

ServiceResolver = Callable[[str], Any]

_service_resolver: ServiceResolver | None = None


def register_payment_service_resolver(resolver: ServiceResolver | None) -> None:
    """Install the runtime lookup from provider service key to service instance."""

    global _service_resolver
    _service_resolver = resolver


def _resolve_provider_service(provider: str) -> Any | None:
    if _service_resolver is None:
        return None
    from bot.payment_providers.registry import get_provider_spec

    spec = get_provider_spec(provider)
    service_key = getattr(spec, "service_key", None) if spec is not None else None
    if not service_key:
        return None
    try:
        return _service_resolver(str(service_key))
    except Exception:
        logger.exception("Failed to resolve payment service %s", service_key)
        return None


async def _cancel_provider_invoice(service: Any, provider_payment_id: str) -> bool:
    for attr in ("cancel_pending_bill", "cancel_pending_checkout", "cancel_payment"):
        cancel = getattr(service, attr, None)
        if not callable(cancel):
            continue
        try:
            result = await cancel(provider_payment_id)
        except Exception:
            logger.exception(
                "Provider service %s failed to cancel invoice %s.",
                type(service).__name__,
                provider_payment_id,
            )
            return False
        if isinstance(result, tuple):
            return bool(result and result[0])
        return bool(result)
    return False


def _snapshot(payment: Any) -> SimpleNamespace:
    return SimpleNamespace(
        payment_id=int(payment.payment_id),
        provider=str(getattr(payment, "provider", "") or ""),
        provider_payment_id=str(
            getattr(payment, "provider_payment_id", None)
            or getattr(payment, "yookassa_payment_id", None)
            or ""
        ).strip(),
    )


async def supersede_pending_promo_payments(
    session: AsyncSession,
    payment: Any,
) -> int:
    """Cancel the user's older pending invoices carrying the same promo code.

    Returns the number of invoices retired. Provider cancellations are
    best-effort: an invoice that cannot be canceled stays pending and keeps
    reserving its promo slot, which is the safe direction.
    """

    promo_code_id = getattr(payment, "promo_code_id", None)
    if promo_code_id is None:
        return 0
    earlier = await payment_checkout_dal.list_earlier_pending_payments_with_promo(
        session, payment
    )
    if not earlier:
        return 0

    snapshots = [_snapshot(item) for item in earlier]
    replacement_id = int(payment.payment_id)
    # Release row locks before provider HTTP calls, mirroring the hosted
    # checkout supersede flow. The replacement payment must already be
    # committed by the caller.
    await session.rollback()

    retired = 0
    for previous in snapshots:
        previous_id = previous.payment_id
        provider_payment_id = previous.provider_payment_id
        service = _resolve_provider_service(previous.provider) if provider_payment_id else None

        canceled = False
        if provider_payment_id:
            if service is None or not getattr(service, "configured", True):
                logger.warning(
                    "Cannot cancel superseded %s invoice %s: provider service unavailable.",
                    previous.provider,
                    previous_id,
                )
                continue
            canceled = await _cancel_provider_invoice(service, provider_payment_id)
            if not canceled:
                logger.warning(
                    "Provider kept superseded %s invoice %s active.",
                    previous.provider,
                    previous_id,
                )
                continue
        else:
            # No externally payable invoice exists (internal/balance payment);
            # nothing can be charged, so the pending row is safe to retire.
            canceled = True

        await payment_dal.transition_provider_payment_to_terminal(
            session,
            previous_id,
            provider_payment_id or str(previous_id),
            "canceled",
            failure_kind="superseded_checkout",
            provider_cancellation_party="merchant",
            provider_cancellation_reason=f"superseded_by_payment_{replacement_id}",
            suppress_failure_notification=True,
        )
        await session.commit()
        retired += 1
        logger.info(
            "Canceled superseded %s invoice %s after promo checkout %s.",
            previous.provider,
            previous_id,
            replacement_id,
        )
    return retired
