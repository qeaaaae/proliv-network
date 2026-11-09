"""User-side giveaway participation.

Entry points: the ``?start=giveaway_<id>`` deep link attached to a published
giveaway post and the ``giveaway:retry:<id>`` re-check button shown when a
condition failed. Conditions are fixed: member of the required channel (when
``REQUIRED_CHANNEL_ID`` is configured) plus an active subscription. Both are
re-checked on every attempt - a cached verification flag is never trusted for
contest semantics.
"""

import logging
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any

from aiogram import Bot, F, Router, types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from bot.middlewares.i18n import JsonI18n
from bot.services.giveaway_service import (
    check_giveaway_eligibility,
    refresh_participate_button,
)
from bot.services.subscription_service_impl.core import SubscriptionService
from bot.utils.callback_answer import callback_data, callback_message, safe_answer_callback
from bot.utils.channel_subscription import (
    normalize_required_channel_id,
    resolve_required_channel_link,
)
from config.settings import Settings
from db.dal import giveaway_dal, user_dal
from db.giveaway_models import GIVEAWAY_STATUS_ACTIVE, Giveaway
from db.models import User

logger = logging.getLogger(__name__)

router = Router(name="user_giveaway_router")


def _retry_keyboard(
    _: Callable[..., str],
    giveaway_id: int,
    channel_url: str | None,
    include_subscribe: bool,
) -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if channel_url:
        builder.button(text=_("channel_subscription_join_button"), url=channel_url)
    if include_subscribe:
        builder.button(
            text=_("giveaway_get_subscription_button"), callback_data="main_action:subscribe"
        )
    builder.button(text=_("giveaway_retry_button"), callback_data=f"giveaway:retry:{giveaway_id}")
    builder.adjust(1)
    return builder.as_markup()


async def _run_join(
    *,
    answer: Callable[..., Awaitable[Any]],
    bot: Bot | None,
    session: AsyncSession,
    settings: Settings,
    _: Callable[..., str],
    subscription_service: SubscriptionService,
    db_user: User,
    giveaway_id: int,
) -> bool:
    """Evaluate conditions and register the participant.

    Returns True when the caller may continue its normal flow; False when a
    dedicated prompt was already shown and nothing else should be sent.
    """
    giveaway = await giveaway_dal.get_giveaway(session, giveaway_id)
    if giveaway is None or giveaway.status != GIVEAWAY_STATUS_ACTIVE:
        await answer(_("giveaway_not_active"))
        return True

    eligibility = await check_giveaway_eligibility(
        bot, session, settings, subscription_service, db_user
    )
    if eligibility.check_failed:
        await answer(
            _("giveaway_check_failed"),
            reply_markup=_retry_keyboard(_, giveaway_id, None, include_subscribe=False),
        )
        return False

    if eligibility.channel_configured and not eligibility.channel_member:
        giveaway_channel_id = normalize_required_channel_id(settings.GIVEAWAY_CHANNEL_ID)
        channel_url = await resolve_required_channel_link(
            bot, giveaway_channel_id, settings.GIVEAWAY_CHANNEL_LINK
        )
        await answer(
            _("giveaway_need_channel"),
            reply_markup=_retry_keyboard(_, giveaway_id, channel_url, include_subscribe=False),
        )
        return False

    gate_channel_id = normalize_required_channel_id(settings.REQUIRED_CHANNEL_ID)
    giveaway_channel_id = normalize_required_channel_id(settings.GIVEAWAY_CHANNEL_ID)
    if (
        eligibility.channel_configured
        and gate_channel_id is not None
        and gate_channel_id == giveaway_channel_id
    ):
        # The giveaway channel is the same one the global channel gate checks:
        # fresh membership confirmed - persist the flag so the gate stops
        # blocking this user's other callbacks (e.g. "get a subscription").
        # Commit eagerly: the no-subscription branch returns before join commit.
        try:
            await user_dal.update_user(
                session,
                int(db_user.user_id),
                {
                    "channel_subscription_checked_at": datetime.now(UTC),
                    "channel_subscription_verified_for": gate_channel_id,
                    "channel_subscription_verified": True,
                },
            )
            await session.commit()
        except Exception as error:
            await session.rollback()
            logger.exception(
                "Giveaway join: failed to persist channel flag for user %s: %s",
                db_user.user_id,
                error,
            )

    if not eligibility.has_subscription:
        text = (
            _("giveaway_need_paid_subscription")
            if eligibility.trial_subscription
            else _("giveaway_need_subscription")
        )
        await answer(
            text,
            reply_markup=_retry_keyboard(_, giveaway_id, None, include_subscribe=True),
        )
        return False

    joined, _already = await giveaway_dal.add_participant(
        session, giveaway_id, int(db_user.user_id)
    )
    try:
        await session.commit()
    except Exception as error:
        await session.rollback()
        logger.exception(
            "Giveaway %s join commit failed for user %s: %s",
            giveaway_id,
            db_user.user_id,
            error,
        )
        await answer(_("error_occurred_try_again"))
        return True

    if joined:
        await _update_participate_counter(bot, session, giveaway, _("giveaway_participate_button"))
        await answer(_("giveaway_joined"))
        logger.info("User %s joined giveaway %s.", db_user.user_id, giveaway_id)
    else:
        await answer(_("giveaway_already_joined"))
    return True


async def _update_participate_counter(
    bot: Bot | None,
    session: AsyncSession,
    giveaway: Giveaway,
    label: str,
) -> None:
    """Refresh the published post's button with the display participant count."""
    display = await giveaway_dal.bump_display_count(session, giveaway)
    try:
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.warning("Giveaway %s display count commit failed: %s", giveaway.giveaway_id, e)
        return
    await refresh_participate_button(bot, giveaway, label, display)


async def join_giveaway_from_start(
    message: types.Message,
    *,
    session: AsyncSession,
    settings: Settings,
    i18n: JsonI18n | None,
    current_lang: str,
    subscription_service: SubscriptionService,
    db_user: User | None,
    giveaway_id: int,
) -> bool:
    """Deep-link join from /start; False means a prompt was shown - stop the flow."""
    if db_user is None:
        return True
    _ = (
        (lambda key, **kwargs: i18n.gettext(current_lang, key, **kwargs))
        if i18n
        else (lambda key, **kwargs: key)
    )
    bot = message.bot if hasattr(message, "bot") else None
    return await _run_join(
        answer=message.answer,
        bot=bot,
        session=session,
        settings=settings,
        _=_,
        subscription_service=subscription_service,
        db_user=db_user,
        giveaway_id=giveaway_id,
    )


@router.callback_query(F.data.regexp(r"^giveaway:retry:\d+$"))
async def giveaway_retry_handler(
    callback: types.CallbackQuery,
    settings: Settings,
    i18n_data: dict,
    subscription_service: SubscriptionService,
    session: AsyncSession,
) -> None:
    current_lang = i18n_data.get("current_language", settings.DEFAULT_LANGUAGE)
    i18n: JsonI18n | None = i18n_data.get("i18n_instance")
    _ = (
        (lambda key, **kwargs: i18n.gettext(current_lang, key, **kwargs))
        if i18n
        else (lambda key, **kwargs: key)
    )

    try:
        giveaway_id = int(callback_data(callback).rsplit(":", 1)[1])
    except (IndexError, ValueError):
        await safe_answer_callback(callback, _("error_occurred_try_again"), show_alert=True)
        return

    db_user = await user_dal.get_user_by_telegram_id(session, callback.from_user.id)
    if db_user is None:
        await safe_answer_callback(callback, _("error_occurred_try_again"), show_alert=True)
        return

    target_message = callback.message

    async def answer(
        text: str, reply_markup: types.InlineKeyboardMarkup | None = None
    ) -> types.Message | None:
        if target_message is not None:
            return await target_message.answer(text, reply_markup=reply_markup)
        if callback.bot is not None:
            return await callback.bot.send_message(
                callback.from_user.id, text, reply_markup=reply_markup
            )
        return None

    bot = None
    if callback.bot is not None:
        bot = callback.bot
    elif target_message is not None:
        bot = callback_message(callback).bot

    joined_or_continue = await _run_join(
        answer=answer,
        bot=bot,
        session=session,
        settings=settings,
        _=_,
        subscription_service=subscription_service,
        db_user=db_user,
        giveaway_id=giveaway_id,
    )
    if joined_or_continue:
        await safe_answer_callback(callback)
    else:
        await safe_answer_callback(callback, _("giveaway_retry_failed"), show_alert=True)
