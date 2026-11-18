"""Trial-conversion one-off broadcast.

Mints a personal single-use -30% promo code for every user currently on an
active trial and DMs them an "Активировать" button that runs the usual
``?start=promo_<code>`` deep-link flow (promo auto-applies, checkout opens
with the discount).

Modes (env):
  (default)      dry-run: lists targets, writes nothing, sends nothing
  TEST_ADMIN=1   mints real personal codes bound to admin accounts and sends
                 the same message to admin chats only
  APPLY=1        sends to the whole active-trial cohort; dedup marker
                 'trial_convert_offer' in subscription_notifications

Run inside the bot/backend container:
  cd /app/backend && python scripts/trial_convert_broadcast.py
"""

import asyncio
import logging
import os
from datetime import UTC, datetime, timedelta

from aiogram import types
from sqlalchemy import func, select

from bot.app.factories.telegram_bot import create_telegram_bot
from bot.services.message_audit import log_user_message_delivery
from bot.services.promo_code_service import PromoCodeService
from bot.services.promo_effects import PromoEffects
from bot.services.settings_override_service import load_overrides_from_db
from bot.services.user_notification_policy import (
    UserNotificationCategory,
    telegram_recipient,
    user_notification_channel_allowed,
)
from bot.services.winback_survey import promo_still_redeemable, resolve_admin_chat_ids
from bot.utils.mini_app_url import bot_start_deep_link
from config.settings import Settings
from db.dal import subscription_dal, user_dal
from db.database_setup import init_db_connection
from db.models import PromoCode, Subscription, User

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("trial_convert")

DISCOUNT_PERCENT = 30.0
PROMO_VALID_DAYS = 7
PROMO_ORIGIN = "trial_convert"
SENT_KEY = "trial_convert_offer"
SEND_DELAY_SECONDS = 0.4

E_TRIAL = '<tg-emoji emoji-id="5897607722295103204">🧪</tg-emoji>'
E_TAG = '<tg-emoji emoji-id="5854776233950188167">🏷</tg-emoji>'
E_DOWN = '<tg-emoji emoji-id="5875008416132370818">👇</tg-emoji>'

TEST_ADMIN = os.environ.get("TEST_ADMIN") == "1"
APPLY = os.environ.get("APPLY") == "1"


def message_text(code: str, valid_until: datetime | None) -> str:
    expires = (
        f", действует до {valid_until.strftime('%d.%m.%Y')}"
        if isinstance(valid_until, datetime)
        else ""
    )
    return (
        f"{E_TRIAL} <b>Как вам пробный период?</b>\n\n"
        "Если Proliv Network уже пригодился - держите персональную скидку "
        "<b>-30%</b> на покупку подписки:\n\n"
        f"{E_TAG} <code>{code}</code>\n\n"
        f"Код только для вашего аккаунта{expires}. "
        f"Жмите «Активировать» - скидка подставится сама {E_DOWN}"
    )


def offer_markup(bot_username: str, code: str) -> types.InlineKeyboardMarkup | None:
    deep_link = bot_start_deep_link(bot_username, f"promo_{code}")
    if not deep_link:
        return None
    return types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="Активировать", url=deep_link)]
        ]
    )


async def find_existing_promo(session, user_id: int) -> PromoCode | None:
    """Latest still-redeemable trial_convert promo for the user, if any."""
    result = await session.execute(
        select(PromoCode)
        .where(PromoCode.user_id == int(user_id), PromoCode.origin == PROMO_ORIGIN)
        .order_by(PromoCode.promo_code_id.desc())
    )
    for promo in result.scalars():
        if promo_still_redeemable(promo):
            return promo
    return None


async def ensure_promo(session, user: User) -> PromoCode:
    promo = await find_existing_promo(session, int(user.user_id))
    if promo is not None:
        return promo
    return await PromoCodeService.issue_code(
        session,
        effects=PromoEffects(
            discount_percent=DISCOUNT_PERCENT,
            applies_to="subscription",
        ),
        code=None,
        max_activations=1,
        valid_until=datetime.now(UTC) + timedelta(days=PROMO_VALID_DAYS),
        origin=PROMO_ORIGIN,
        created_by_admin_id=None,
        user_id=int(user.user_id),
    )


async def send_offer(bot, *, chat_id: int, code: str, valid_until, bot_username: str) -> bool:
    try:
        await bot.send_message(
            chat_id,
            message_text(code, valid_until),
            parse_mode="HTML",
            reply_markup=offer_markup(bot_username, code),
        )
        return True
    except Exception:
        logger.exception("send failed chat_id=%s", chat_id)
        return False


async def load_trial_targets(session) -> list[tuple[Subscription, User]]:
    now = datetime.now(UTC)
    stmt = (
        select(Subscription, User)
        .join(User, Subscription.user_id == User.user_id)
        .where(
            Subscription.is_active == True,  # noqa: E712
            Subscription.end_date > now,
            func.lower(func.coalesce(Subscription.provider, "")) == "trial",
            User.is_banned == False,  # noqa: E712
        )
        .order_by(Subscription.user_id.asc(), Subscription.end_date.desc())
    )
    by_user: dict[int, tuple[Subscription, User]] = {}
    for sub, user in (await session.execute(stmt)).all():
        uid = int(sub.user_id)
        if uid not in by_user:
            by_user[uid] = (sub, user)
    return list(by_user.values())


async def run() -> None:
    settings = Settings()
    session_factory = init_db_connection(settings)
    await load_overrides_from_db(settings, session_factory)
    bot = create_telegram_bot(settings)
    try:
        me = await bot.get_me()
        bot_username = me.username or ""
        logger.info("bot username: @%s", bot_username)
        await _dispatch(bot, settings, session_factory, bot_username)
    finally:
        await bot.session.close()


async def _dispatch(bot, settings, session_factory, bot_username: str) -> None:
    if TEST_ADMIN:
        async with session_factory() as session:
            chat_ids = await resolve_admin_chat_ids(session, settings)
        logger.info("TEST_ADMIN: %d admin chats", len(chat_ids))
        for chat_id in chat_ids:
            async with session_factory() as session:
                try:
                    user = await user_dal.get_user_by_telegram_id(session, chat_id)
                    if user is not None:
                        promo = await ensure_promo(session, user)
                        code, valid_until = promo.code, promo.valid_until
                    else:
                        code, valid_until = "PREVIEWONLY", None
                    ok = await send_offer(
                        bot,
                        chat_id=chat_id,
                        code=str(code),
                        valid_until=valid_until,
                        bot_username=bot_username,
                    )
                    if ok:
                        await session.commit()
                        logger.info("  sent to admin chat %s (code %s)", chat_id, code)
                    else:
                        await session.rollback()
                        logger.warning("  FAILED admin chat %s", chat_id)
                except Exception:
                    await session.rollback()
                    logger.exception("  FAILED admin chat %s", chat_id)
            await asyncio.sleep(SEND_DELAY_SECONDS)
        return

    async with session_factory() as session:
        targets = await load_trial_targets(session)
    logger.info("active-trial targets: %d", len(targets))

    if not APPLY:
        for sub, user in targets:
            already = None
            async with session_factory() as session:
                already = await subscription_dal.has_subscription_notification(
                    session, int(sub.subscription_id), SENT_KEY
                )
            logger.info(
                "  user_id=%s tg=%s @%s end=%s notified=%s",
                user.user_id,
                user.telegram_id,
                user.username,
                sub.end_date,
                already,
            )
        logger.info("dry run - set APPLY=1 to send")
        return

    sent = skipped = failed = 0
    for sub, user in targets:
        async with session_factory() as session:
            try:
                if await subscription_dal.has_subscription_notification(
                    session, int(sub.subscription_id), SENT_KEY
                ):
                    skipped += 1
                    continue
                if not user_notification_channel_allowed(
                    user, UserNotificationCategory.MARKETING, "telegram"
                ):
                    skipped += 1
                    logger.info("  skip user %s - marketing opt-out", user.user_id)
                    continue
                chat_id = telegram_recipient(user)
                if chat_id is None:
                    skipped += 1
                    logger.info("  skip user %s - no reachable telegram", user.user_id)
                    continue
                promo = await ensure_promo(session, user)
                ok = await send_offer(
                    bot,
                    chat_id=chat_id,
                    code=str(promo.code),
                    valid_until=promo.valid_until,
                    bot_username=bot_username,
                )
                if not ok:
                    await session.rollback()
                    failed += 1
                    continue
                await subscription_dal.record_subscription_notification(
                    session, int(sub.subscription_id), SENT_KEY
                )
                await log_user_message_delivery(
                    session,
                    target_user_id=int(user.user_id),
                    event_type="trial_convert_offer",
                    channel="telegram",
                    recipient=str(chat_id),
                    content=f"promo={promo.code} discount={DISCOUNT_PERCENT:g}%",
                )
                await session.commit()
                sent += 1
                logger.info("  sent user %s code %s", user.user_id, promo.code)
            except Exception:
                await session.rollback()
                failed += 1
                logger.exception("  FAILED user %s", user.user_id)
        await asyncio.sleep(SEND_DELAY_SECONDS)
    logger.info("done: sent=%d skipped=%d failed=%d", sent, skipped, failed)


if __name__ == "__main__":
    asyncio.run(run())
