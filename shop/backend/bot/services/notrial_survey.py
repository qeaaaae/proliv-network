"""Survey for registered users who never activated anything.

Users registered for at least ``NOTRIAL_MIN_AGE`` with zero subscription
rows (no trial, no paid plan) get a one-time "why haven't you tried the
free period" survey with reason buttons. Answers are forwarded to admin
DMs; the "already use another VPN" answer mints a personal single-use
promo code as a switch incentive.

Send/answer dedup reuses ``message_logs`` events - unlike the win-back
survey these users have no subscription row to attach a marker to.
"""

import logging
from datetime import UTC, datetime, timedelta
from html import escape

from aiogram import Bot, types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.middlewares.i18n import JsonI18n
from bot.services.message_audit import log_user_message_delivery
from bot.services.promo_code_service import PromoCodeService
from bot.services.promo_effects import PromoEffects
from bot.services.user_notification_policy import telegram_recipient
from bot.services.winback_survey import (
    admin_user_display,
    resolve_admin_chat_ids,
    survey_eligible_user,
)
from config.settings import Settings
from db.models import MessageLog, PromoCode, Subscription, User

logger = logging.getLogger(__name__)

NOTRIAL_SENT_EVENT = "notrial_survey_sent"
NOTRIAL_RESPONSE_EVENT = "notrial_survey_response"
NOTRIAL_MIN_AGE = timedelta(days=3)
NOTRIAL_DISCOUNT_PERCENT = 10.0
NOTRIAL_PROMO_VALID_DAYS = 7
NOTRIAL_PROMO_ORIGIN = "notrial"

REASON_NO_NEED = "no_need"
REASON_CONFUSING = "confusing"
REASON_OTHER_VPN = "other_vpn"
REASON_OTHER = "other"
REASON_LABEL_KEYS = {
    REASON_NO_NEED: "notrial_reason_no_need",
    REASON_CONFUSING: "notrial_reason_confusing",
    REASON_OTHER_VPN: "notrial_reason_other_vpn",
    REASON_OTHER: "notrial_reason_other",
}


async def find_survey_targets(session: AsyncSession, now: datetime) -> list[User]:
    """Users old enough for the survey who never had any subscription."""
    has_subscription = exists(
        select(Subscription.subscription_id).where(Subscription.user_id == User.user_id)
    )
    result = await session.execute(
        select(User)
        .where(
            User.registration_date <= now - NOTRIAL_MIN_AGE,
            User.is_banned == False,
            User.telegram_id.is_not(None),
            ~has_subscription,
        )
        .order_by(User.registration_date.asc())
    )
    return list(result.scalars().all())


async def has_notrial_event(session: AsyncSession, user_id: int, event_type: str) -> bool:
    result = await session.execute(
        select(MessageLog.log_id)
        .where(
            MessageLog.target_user_id == int(user_id),
            MessageLog.event_type == event_type,
        )
        .limit(1)
    )
    return result.scalar_one_or_none() is not None


async def survey_already_sent(session: AsyncSession, user_id: int) -> bool:
    return await has_notrial_event(session, user_id, NOTRIAL_SENT_EVENT)


async def survey_already_answered(session: AsyncSession, user_id: int) -> bool:
    return await has_notrial_event(session, user_id, NOTRIAL_RESPONSE_EVENT)


def survey_markup(
    i18n: JsonI18n, lang: str, user_id: int, settings: Settings
) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    for reason, label_key in REASON_LABEL_KEYS.items():
        builder.button(
            text=i18n.gettext(lang, label_key),
            callback_data=f"notrial:r:{reason}:{user_id}",
        )
    builder.adjust(1)
    mini_app_url = getattr(settings, "SUBSCRIPTION_MINI_APP_URL", "") or ""
    if mini_app_url:
        builder.row(
            types.InlineKeyboardButton(
                text=i18n.gettext(lang, "notrial_try_button"),
                web_app=types.WebAppInfo(url=mini_app_url),
            )
        )
    return builder


async def send_survey_prompt(
    *,
    bot: Bot | None,
    i18n: JsonI18n,
    settings: Settings,
    session: AsyncSession,
    user: User,
    sent_at: datetime | None = None,
) -> bool:
    if bot is None or not survey_eligible_user(user):
        return False
    if sent_at is None:
        sent_at = datetime.now(UTC)
    lang = getattr(user, "language_code", None) or settings.DEFAULT_LANGUAGE
    chat_id = telegram_recipient(user)
    if chat_id is None:
        return False
    user_id = int(user.user_id)
    try:
        await bot.send_message(
            chat_id,
            i18n.gettext(lang, "notrial_survey_prompt"),
            reply_markup=survey_markup(i18n, lang, user_id, settings).as_markup(),
        )
    except Exception:
        logger.exception("Failed to send no-trial survey to Telegram user %s", chat_id)
        return False
    await log_user_message_delivery(
        session,
        target_user_id=user_id,
        event_type=NOTRIAL_SENT_EVENT,
        channel="telegram",
        recipient=str(chat_id),
        content=f"user_id={user_id}",
    )
    return True


async def notify_notrial_admins(
    *,
    bot: Bot | None,
    session: AsyncSession,
    settings: Settings,
    i18n: JsonI18n,
    user: User | None,
    telegram_id: int,
    detail_lines: list[str],
) -> None:
    if bot is None:
        return
    lang = settings.DEFAULT_LANGUAGE
    details = "\n".join(line for line in detail_lines if line)
    text = i18n.gettext(
        lang,
        "admin_notrial_report",
        user=admin_user_display(user, telegram_id),
        details=escape(details),
    )
    chat_ids = await resolve_admin_chat_ids(session, settings)
    if not chat_ids:
        logger.warning("No-trial survey response has no admin chat ids to notify")
        return
    for chat_id in chat_ids:
        try:
            await bot.send_message(chat_id, text, parse_mode="HTML")
        except Exception:
            logger.warning(
                "Failed to deliver no-trial survey response to admin %s",
                chat_id,
                exc_info=True,
            )


async def issue_notrial_discount(
    session: AsyncSession, user: User, *, now: datetime | None = None
) -> PromoCode:
    """Mint a personal single-use promo code for the "other VPN" answer."""
    if now is None:
        now = datetime.now(UTC)
    return await PromoCodeService.issue_code(
        session,
        effects=PromoEffects(discount_percent=NOTRIAL_DISCOUNT_PERCENT),
        code=None,
        max_activations=1,
        valid_until=now + timedelta(days=NOTRIAL_PROMO_VALID_DAYS),
        origin=NOTRIAL_PROMO_ORIGIN,
        created_by_admin_id=None,
        user_id=int(user.user_id),
    )


async def find_notrial_promo(session: AsyncSession, user_id: int) -> PromoCode | None:
    """Latest no-trial promo code ever minted for this user (one per user)."""
    result = await session.execute(
        select(PromoCode)
        .where(
            PromoCode.user_id == int(user_id),
            PromoCode.origin == NOTRIAL_PROMO_ORIGIN,
        )
        .order_by(PromoCode.promo_code_id.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def record_notrial_response(session: AsyncSession, user: User, *, content: str) -> None:
    await log_user_message_delivery(
        session,
        target_user_id=int(user.user_id),
        event_type=NOTRIAL_RESPONSE_EVENT,
        channel="telegram",
        content=content,
    )
