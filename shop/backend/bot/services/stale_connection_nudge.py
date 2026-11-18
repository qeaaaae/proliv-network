"""Stale-connection nudge for users on an active subscription or trial.

Finds users on an active subscription (paid or trial) who have not
connected for ``STALE_CONNECTION_AFTER`` (or never connected since the
subscription started) and sends a one-time "something not working?" help
message with connect / support / dismiss buttons. Delivery dedup uses the
``subscription_notifications`` marker ``stale_connection_notice`` per
subscription row, matching the win-back survey pattern.
"""

import logging
from datetime import UTC, datetime, timedelta

from aiogram import Bot, types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.middlewares.i18n import JsonI18n
from bot.services.message_audit import log_user_message_delivery
from bot.services.subscription_service_impl.entitlement_helpers import (
    subscription_is_trial,
)
from bot.services.user_notification_policy import (
    UserNotificationCategory,
    telegram_recipient,
    user_notification_channel_allowed,
)
from bot.utils.install_links import bot_install_guide_url
from config.settings import Settings
from config.support_links import normalize_support_link
from db.dal import subscription_dal
from db.models import Subscription, User

logger = logging.getLogger(__name__)

STALE_SENT_KEY = "stale_connection_notice"
STALE_CONNECTION_AFTER = timedelta(days=2)
CLOSE_CALLBACK = "stale_conn:close"


async def find_nudge_targets(session: AsyncSession, now: datetime) -> list[Subscription]:
    """Active subscriptions (paid or trial) whose owner went quiet.

    ``COALESCE(last_connected_at, start_date)`` makes "never connected"
    subscriptions stale once their grace period (subscription age) passes
    the threshold; fresh subscriptions get time to set up first.
    """
    threshold = now - STALE_CONNECTION_AFTER
    result = await session.execute(
        select(Subscription)
        .join(User, Subscription.user_id == User.user_id)
        .where(
            Subscription.is_active == True,
            Subscription.end_date > now,
            func.coalesce(Subscription.last_connected_at, Subscription.start_date) < threshold,
            User.is_banned == False,
        )
        .options(selectinload(Subscription.user))
        .order_by(Subscription.end_date.asc())
    )
    return list(result.scalars().all())


def nudge_message_key(sub: Subscription) -> str:
    """Trial users get wording that does not claim the sub is paid."""
    return (
        "stale_connection_notice_trial"
        if subscription_is_trial(sub)
        else "stale_connection_notice"
    )


def nudge_eligible_user(user: User | None) -> bool:
    """Telegram-reachable user who has not opted out of subscription notices."""
    if user is None or bool(getattr(user, "is_banned", False)):
        return False
    if not user_notification_channel_allowed(
        user, UserNotificationCategory.SUBSCRIPTIONS, "telegram"
    ):
        return False
    return telegram_recipient(user) is not None


def nudge_markup(
    i18n: JsonI18n, lang: str, settings: Settings
) -> InlineKeyboardBuilder:
    def _(key: str) -> str:
        return i18n.gettext(lang, key)

    builder = InlineKeyboardBuilder()
    first_row: list[types.InlineKeyboardButton] = []
    install_url = bot_install_guide_url(settings) or getattr(
        settings, "SUBSCRIPTION_MINI_APP_URL", None
    )
    if install_url:
        first_row.append(
            types.InlineKeyboardButton(
                text=_("connect_button"),
                web_app=types.WebAppInfo(url=install_url),
            )
        )
    support_link = normalize_support_link(settings.support_settings.link)
    if support_link:
        first_row.append(
            types.InlineKeyboardButton(
                text=_("stale_connection_support_button"), url=support_link
            )
        )
    if first_row:
        builder.row(*first_row)
    builder.row(
        types.InlineKeyboardButton(
            text=_("stale_connection_close_button"),
            callback_data=CLOSE_CALLBACK,
        )
    )
    return builder


async def send_nudge(
    *,
    bot: Bot | None,
    i18n: JsonI18n,
    settings: Settings,
    session: AsyncSession,
    sub: Subscription,
    sent_at: datetime | None = None,
) -> bool:
    user = getattr(sub, "user", None)
    if bot is None or not nudge_eligible_user(user):
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
            i18n.gettext(lang, nudge_message_key(sub)),
            reply_markup=nudge_markup(i18n, lang, settings).as_markup(),
        )
    except Exception:
        logger.exception("Failed to send stale-connection nudge to Telegram user %s", chat_id)
        return False
    await subscription_dal.record_subscription_notification(
        session, subscription_id, STALE_SENT_KEY, sent_at=sent_at
    )
    await log_user_message_delivery(
        session,
        target_user_id=int(sub.user_id),
        event_type="stale_connection_notice",
        channel="telegram",
        recipient=str(chat_id),
        content=f"subscription_id={subscription_id}",
    )
    return True
