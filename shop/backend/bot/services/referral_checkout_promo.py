"""Personal checkout promo for invited users (referral friend discount).

An invited user receives a deterministic single-use personal promo code that
applies ``REFERRAL_FRIEND_DISCOUNT_PERCENT`` to a subscription purchase. The
code is minted lazily on the first checkout suggestion inside its own
transaction, so a read-only account payload can never leak an uncommitted code.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.services.promo_effects import PROMO_APPLIES_TO_SUBSCRIPTION
from bot.services.registration_invite_gate import referral_program_enabled
from config.settings import Settings, get_settings
from db import database_setup
from db.dal import promo_code_dal, user_dal
from db.models import PromoCode
from db.restore_guard import RestoreAwareAsyncSession

if TYPE_CHECKING:
    from bot.infra.promo_policies import PromoCheckoutSuggestionContext

logger = logging.getLogger(__name__)

_REFERRAL_PROMO_ORIGIN = "referral"


def referral_friend_discount_percent(settings: Settings) -> float:
    try:
        return max(0.0, float(settings.REFERRAL_FRIEND_DISCOUNT_PERCENT or 0))
    except (TypeError, ValueError):
        return 0.0


def referral_friend_promo_code(user_id: int) -> str:
    return f"RF{int(user_id)}"


def _standalone_session_factory() -> async_sessionmaker[AsyncSession] | None:
    engine = database_setup.async_engine
    if engine is None:
        return None
    return async_sessionmaker(
        bind=engine,
        class_=RestoreAwareAsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


async def _mint_referral_friend_promo(
    session: AsyncSession,
    *,
    user_id: int,
    discount_percent: float,
) -> PromoCode | None:
    code = referral_friend_promo_code(user_id)
    existing = await promo_code_dal.get_promo_code_by_code(session, code)
    if existing is not None:
        return existing
    try:
        promo = await promo_code_dal.create_promo_code(
            session,
            {
                "code": code,
                "bonus_days": 0,
                "discount_percent": discount_percent,
                "applies_to": PROMO_APPLIES_TO_SUBSCRIPTION,
                "origin": _REFERRAL_PROMO_ORIGIN,
                "user_id": int(user_id),
                "max_activations": 1,
                "is_active": True,
            },
        )
        await session.commit()
        return promo
    except IntegrityError:
        # Lost a concurrent mint race; the winning transaction owns the row.
        await session.rollback()
        return await promo_code_dal.get_promo_code_by_code(session, code)


async def ensure_referral_friend_promo(
    *,
    user_id: int,
    discount_percent: float,
) -> PromoCode | None:
    """Return the user's usable referral promo, minting it in a committed session."""

    factory = _standalone_session_factory()
    if factory is None:
        logger.warning(
            "Referral promo mint skipped for user %s: database engine is not initialized",
            user_id,
        )
        return None
    async with factory() as session:
        try:
            promo = await _mint_referral_friend_promo(
                session,
                user_id=user_id,
                discount_percent=discount_percent,
            )
        except Exception:
            await session.rollback()
            logger.exception("Failed to mint referral promo for user %s", user_id)
            return None
    return promo


def _referral_promo_usable(promo: PromoCode) -> bool:
    if not bool(getattr(promo, "is_active", False)):
        return False
    if getattr(promo, "archived_at", None) is not None:
        return False
    return int(getattr(promo, "current_activations", 0) or 0) < int(
        getattr(promo, "max_activations", 0) or 0
    )


async def referral_friend_promo_suggestion(
    ctx: PromoCheckoutSuggestionContext,
) -> str | None:
    """Core suggestion provider: personal discount code for invited users."""

    if ctx.sale_mode_base not in (None, "", PROMO_APPLIES_TO_SUBSCRIPTION):
        return None
    settings = get_settings()
    if not referral_program_enabled(settings):
        return None
    discount_percent = referral_friend_discount_percent(settings)
    if discount_percent <= 0:
        return None
    user = await user_dal.get_user_by_id(ctx.session, int(ctx.user_id))
    if user is None or getattr(user, "referred_by_id", None) is None:
        return None
    promo = await ensure_referral_friend_promo(
        user_id=int(user.user_id),
        discount_percent=discount_percent,
    )
    if promo is None or not _referral_promo_usable(promo):
        return None
    return str(promo.code)
