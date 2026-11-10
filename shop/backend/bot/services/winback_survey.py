"""Win-back survey for lapsed subscriptions.

When a user's latest subscription stays expired for ~1 day the bot sends a
short "why did you decide not to renew" survey with three reasons. Answers
are forwarded to every admin DM; the "too expensive" answer also mints a
personal single-use promo code so the user has a concrete reason to return.

Send dedup reuses the ``subscription_notifications`` table (one survey per
lapsed subscription row), answers are stored in ``message_logs``.
"""

import logging
from datetime import UTC, datetime, timedelta
from html import escape

from aiogram import Bot, types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.text_decorations import html_decoration as hd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.middlewares.i18n import JsonI18n
from bot.services.message_audit import log_user_message_delivery
from bot.services.promo_code_service import PromoCodeService
from bot.services.promo_effects import PromoEffects
from bot.services.user_notification_policy import (
    UserNotificationCategory,
    telegram_recipient,
    user_notification_channel_allowed,
)
from config.settings import Settings
from db.auth_models import AccountRole
from db.dal import subscription_dal
from db.models import PromoCode, Subscription, User

logger = logging.getLogger(__name__)

WINBACK_SENT_KEY = "winback_survey"
WINBACK_ANSWERED_KEY = "winback_survey:answered"
WINBACK_WINDOW_MIN = timedelta(hours=24)
WINBACK_WINDOW_MAX = timedelta(hours=48)
WINBACK_DISCOUNT_PERCENT = 10.0
WINBACK_PROMO_VALID_DAYS = 7
WINBACK_PROMO_ORIGIN = "winback"

REASON_EXPENSIVE = "expensive"
REASON_MISSING_LOCATION = "missing_location"
REASON_UNSTABLE = "unstable"
REASON_LABEL_KEYS = {
    REASON_EXPENSIVE: "winback_reason_expensive",
    REASON_MISSING_LOCATION: "winback_reason_missing_location",
    REASON_UNSTABLE: "winback_reason_unstable",
}


async def find_survey_targets(session: AsyncSession, now: datetime) -> list[Subscription]:
    """Latest lapsed subscription per eligible user, expired 24-48h ago."""
    result = await session.execute(
        select(Subscription)
        .join(User, Subscription.user_id == User.user_id)
        .where(
            Subscription.skip_notifications == False,
            Subscription.end_date > now - WINBACK_WINDOW_MAX,
            Subscription.end_date <= now - WINBACK_WINDOW_MIN,
            User.is_banned == False,
        )
        .options(selectinload(Subscription.user))
        .order_by(Subscription.end_date.desc())
    )
    latest_by_user: dict[int, Subscription] = {}
    for sub in result.scalars().all():
        user_id = int(getattr(sub, "user_id", 0) or 0)
        if user_id and user_id not in latest_by_user:
            latest_by_user[user_id] = sub
    targets = list(latest_by_user.values())
    if not targets:
        return []
    covered_until = await subscription_dal.get_latest_active_end_dates(
        session, set(latest_by_user), now=now
    )
    return [sub for sub in targets if (covered_until.get(int(sub.user_id)) or now) <= now]


def survey_eligible_user(user: User | None) -> bool:
    """Telegram-reachable user who has not opted out of marketing pings."""
    if user is None or bool(getattr(user, "is_banned", False)):
        return False
    if not user_notification_channel_allowed(user, UserNotificationCategory.MARKETING, "telegram"):
        return False
    return telegram_recipient(user) is not None


def survey_markup(
    i18n: JsonI18n, lang: str, subscription_id: int, settings: Settings
) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    for reason, label_key in REASON_LABEL_KEYS.items():
        builder.button(
            text=i18n.gettext(lang, label_key),
            callback_data=f"winback:r:{reason}:{subscription_id}",
        )
    builder.adjust(1)
    mini_app_url = getattr(settings, "SUBSCRIPTION_MINI_APP_URL", "") or ""
    if mini_app_url:
        builder.row(
            types.InlineKeyboardButton(
                text=i18n.gettext(lang, "winback_renew_button"),
                web_app=types.WebAppInfo(url=f"{mini_app_url}/purchases"),
            )
        )
    return builder


async def send_survey_prompt(
    *,
    bot: Bot | None,
    i18n: JsonI18n,
    settings: Settings,
    session: AsyncSession,
    sub: Subscription,
    sent_at: datetime | None = None,
) -> bool:
    user = getattr(sub, "user", None)
    if bot is None or not survey_eligible_user(user):
        return False
    if sent_at is None:
        sent_at = datetime.now(UTC)
    lang = getattr(user, "language_code", None) or settings.DEFAULT_LANGUAGE
    chat_id = telegram_recipient(user)
    if chat_id is None:
        return False
    subscription_id = int(sub.subscription_id)
    try:
        await bot.send_message(
            chat_id,
            i18n.gettext(lang, "winback_survey_prompt"),
            reply_markup=survey_markup(i18n, lang, subscription_id, settings).as_markup(),
        )
    except Exception:
        logger.exception("Failed to send win-back survey to Telegram user %s", chat_id)
        return False
    await subscription_dal.record_subscription_notification(
        session, subscription_id, WINBACK_SENT_KEY, sent_at=sent_at
    )
    await log_user_message_delivery(
        session,
        target_user_id=int(sub.user_id),
        event_type="winback_survey_sent",
        channel="telegram",
        recipient=str(chat_id),
        content=f"subscription_id={subscription_id}",
    )
    return True


async def resolve_admin_chat_ids(session: AsyncSession, settings: Settings) -> list[int]:
    """Telegram chat ids of owner/admin accounts plus raw ADMIN_IDS."""
    chat_ids: set[int] = set()
    result = await session.execute(
        select(User.telegram_id)
        .join(AccountRole, AccountRole.user_id == User.user_id)
        .where(
            AccountRole.role.in_(("owner", "admin")),
            AccountRole.revoked_at.is_(None),
            User.telegram_id.is_not(None),
            User.is_banned.is_(False),
        )
        .distinct()
    )
    for telegram_id in result.scalars().all():
        if telegram_id is not None:
            chat_ids.add(int(telegram_id))
    for admin_id in settings.ADMIN_IDS:
        chat_ids.add(int(admin_id))
    return sorted(chat_ids)


def admin_user_display(user: User | None, telegram_id: int) -> str:
    if user is None:
        return hd.quote(f"tg:{telegram_id}")
    name_parts = [
        str(part).strip()
        for part in (
            getattr(user, "first_name", None),
            getattr(user, "last_name", None),
        )
        if part and str(part).strip()
    ]
    display = " ".join(name_parts) if name_parts else ""
    username = str(getattr(user, "username", "") or "").strip().lstrip("@")
    if username:
        display = f"{display} @{username}".strip()
    if not display:
        display = f"tg:{telegram_id}"
    return f"{hd.quote(display)} (id {int(user.user_id)})"


async def notify_winback_admins(
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
        "admin_winback_report",
        user=admin_user_display(user, telegram_id),
        details=escape(details),
    )
    chat_ids = await resolve_admin_chat_ids(session, settings)
    if not chat_ids:
        logger.warning("Win-back survey response has no admin chat ids to notify")
        return
    for chat_id in chat_ids:
        try:
            await bot.send_message(chat_id, text, parse_mode="HTML")
        except Exception:
            logger.warning(
                "Failed to deliver win-back survey response to admin %s",
                chat_id,
                exc_info=True,
            )


async def issue_winback_discount(
    session: AsyncSession, user: User, *, now: datetime | None = None
) -> PromoCode:
    """Mint a personal single-use promo code for the "too expensive" answer."""
    if now is None:
        now = datetime.now(UTC)
    return await PromoCodeService.issue_code(
        session,
        effects=PromoEffects(discount_percent=WINBACK_DISCOUNT_PERCENT),
        code=None,
        max_activations=1,
        valid_until=now + timedelta(days=WINBACK_PROMO_VALID_DAYS),
        origin=WINBACK_PROMO_ORIGIN,
        created_by_admin_id=None,
        user_id=int(user.user_id),
    )


async def find_winback_promo(session: AsyncSession, user_id: int) -> PromoCode | None:
    """Latest win-back promo code ever minted for this user, if any.

    The discount is a one-per-user-ever offer: a fresh code is only minted
    when no win-back code exists at all, so a renewed-then-lapsed user cannot
    farm extra codes from later surveys.
    """
    result = await session.execute(
        select(PromoCode)
        .where(
            PromoCode.user_id == int(user_id),
            PromoCode.origin == WINBACK_PROMO_ORIGIN,
        )
        .order_by(PromoCode.promo_code_id.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


def promo_still_redeemable(promo: PromoCode, now: datetime | None = None) -> bool:
    """Active, unarchived, unexpired code with activations left."""
    if now is None:
        now = datetime.now(UTC)
    if not getattr(promo, "is_active", False):
        return False
    if getattr(promo, "archived_at", None) is not None:
        return False
    valid_until = getattr(promo, "valid_until", None)
    if isinstance(valid_until, datetime):
        until = valid_until if valid_until.tzinfo is not None else valid_until.replace(tzinfo=UTC)
        if until <= now:
            return False
    current = int(getattr(promo, "current_activations", 0) or 0)
    maximum = int(getattr(promo, "max_activations", 0) or 0)
    return maximum <= 0 or current < maximum


async def record_winback_response(session: AsyncSession, user: User, *, content: str) -> None:
    await log_user_message_delivery(
        session,
        target_user_id=int(user.user_id),
        event_type="winback_survey_response",
        channel="telegram",
        content=content,
    )


async def mark_survey_answered(
    session: AsyncSession, subscription_id: int, *, sent_at: datetime | None = None
) -> None:
    await subscription_dal.record_subscription_notification(
        session, int(subscription_id), WINBACK_ANSWERED_KEY, sent_at=sent_at
    )


async def survey_already_answered(session: AsyncSession, subscription_id: int) -> bool:
    return await subscription_dal.has_subscription_notification(
        session, int(subscription_id), WINBACK_ANSWERED_KEY
    )
