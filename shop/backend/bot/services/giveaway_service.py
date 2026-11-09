"""Shared giveaway eligibility checks.

Participation rules (fixed by product): an active *paid* service subscription
(trial subscriptions do not qualify) plus
membership in the giveaway channel (``GIVEAWAY_CHANNEL_ID``; deliberately not
``REQUIRED_CHANNEL_ID`` so the whole bot is not gated). The same rules apply
when a user joins via the ``?start=giveaway_<id>`` deep link. Conditions are
checked only at join; the draw shuffles registered participants as-is.
"""

import logging
import random
from dataclasses import dataclass

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.utils.text_decorations import html_decoration as hd
from sqlalchemy.ext.asyncio import AsyncSession

from bot.services.subscription_service_impl.core import SubscriptionService
from bot.services.subscription_service_impl.entitlement_helpers import (
    subscription_is_trial,
)
from bot.utils.channel_subscription import (
    is_required_channel_access_error,
    normalize_required_channel_id,
)
from config.settings import Settings
from db.dal import giveaway_dal, subscription_dal
from db.giveaway_models import Giveaway
from db.models import User

logger = logging.getLogger(__name__)

_GIVEAWAY_CHANNEL_MEMBER_STATUSES = {"creator", "administrator", "member", "restricted"}


@dataclass
class GiveawayEligibility:
    channel_configured: bool
    channel_member: bool
    has_subscription: bool
    trial_subscription: bool = False
    check_failed: bool = False

    @property
    def ok(self) -> bool:
        return (
            not self.check_failed
            and self.has_subscription
            and (not self.channel_configured or self.channel_member)
        )


async def check_giveaway_eligibility(
    bot: Bot | None,
    session: AsyncSession,
    settings: Settings,
    subscription_service: SubscriptionService,
    db_user: User,
) -> GiveawayEligibility:
    """Fresh (non-cached) eligibility check for giveaway participation."""
    required_channel_id = normalize_required_channel_id(settings.GIVEAWAY_CHANNEL_ID)
    channel_member = False
    check_failed = False

    if required_channel_id is not None:
        telegram_id = db_user.telegram_id
        if bot is None or not telegram_id:
            check_failed = True
        else:
            try:
                member = await bot.get_chat_member(required_channel_id, int(telegram_id))
                status = getattr(member, "status", None)
                status_value = getattr(status, "value", status)
                channel_member = status_value in _GIVEAWAY_CHANNEL_MEMBER_STATUSES
            except TelegramAPIError as error:
                if is_required_channel_access_error(error):
                    logger.error("Giveaway channel check failed (config/access): %s", error)
                    check_failed = True
                else:
                    # "user not found" / not a member: simply not subscribed.
                    channel_member = False

    try:
        subscription = await subscription_dal.get_active_subscription_by_user_id(
            session, int(db_user.user_id)
        )
        has_subscription = subscription is not None and not subscription_is_trial(
            subscription
        )
        trial_subscription = subscription is not None and subscription_is_trial(
            subscription
        )
    except Exception as error:
        logger.exception(
            "Giveaway subscription check failed for user %s: %s", db_user.user_id, error
        )
        has_subscription = False
        trial_subscription = False
        check_failed = True

    return GiveawayEligibility(
        channel_configured=required_channel_id is not None,
        channel_member=channel_member,
        has_subscription=has_subscription,
        trial_subscription=trial_subscription,
        check_failed=check_failed,
    )


def participant_label(user: User) -> str:
    """HTML-safe one-line participant label for admin lists and announcements."""
    if user.username:
        return f"@{user.username}"
    name = user.first_name or user.last_name or ""
    name = name.strip() or f"ID {user.user_id}"
    if user.telegram_id:
        return f'<a href="tg://user?id={user.telegram_id}">{hd.quote(name)}</a>'
    return hd.quote(name)


async def draw_giveaway_winners(
    session: AsyncSession,
    giveaway: Giveaway,
) -> list[tuple[int, User]]:
    """Pick winners from registered participants (conditions checked at join).

    Product rule: no re-verification at draw time - a participant who joined
    stays in the draw even if the subscription ended or the channel was left.
    Banned users are skipped (they cannot receive prizes anyway).
    """
    rows = await giveaway_dal.participant_users(session, int(giveaway.giveaway_id))
    random.shuffle(rows)
    winners_needed = max(1, int(giveaway.winners_count or 3))
    winners: list[tuple[int, User]] = []
    for participant, user in rows:
        if len(winners) >= winners_needed:
            break
        if user.is_banned:
            continue
        place = len(winners) + 1
        await giveaway_dal.set_participant_place(session, participant, place)
        winners.append((place, user))
    return winners


async def refresh_participate_button(
    bot: Bot | None,
    giveaway: Giveaway,
    label: str,
    display_count: int | None,
) -> None:
    """Re-render the published post's button with the current counter."""
    if bot is None or not giveaway.chat_id or not giveaway.message_id:
        return
    try:
        me = await bot.get_me()
        if not me.username:
            return
        from bot.utils.mini_app_url import bot_start_deep_link

        url = bot_start_deep_link(me.username, f"giveaway_{int(giveaway.giveaway_id)}")
        if url is None:
            return
        from bot.keyboards.inline.admin_keyboards import (
            get_giveaway_participate_keyboard,
        )

        await bot.edit_message_reply_markup(
            chat_id=int(giveaway.chat_id),
            message_id=int(giveaway.message_id),
            reply_markup=get_giveaway_participate_keyboard(url, label, display_count),
        )
    except Exception as e:
        logger.warning("Giveaway %s participate counter update failed: %s", giveaway.giveaway_id, e)
