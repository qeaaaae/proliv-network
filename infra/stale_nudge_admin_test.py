"""Stale-connection nudge - admin preview / dry-run.

Modes (env):
  (default)      dry-run: lists current stale-connection targets
                 (active subs - paid or trial - quiet for STALE_CONNECTION_AFTER)
  TEST_ADMIN=1   sends the real nudge message to admin chats only;
                 no subscription_notifications marker is written

Run inside the bot/backend container:
  cd /app && python backend/scripts/stale_nudge_admin_test.py
"""

import asyncio
import logging
import os
from datetime import UTC, datetime

from bot.app.factories.telegram_bot import create_telegram_bot
from bot.middlewares.i18n import get_i18n_instance
from bot.services.settings_override_service import load_overrides_from_db
from bot.services.stale_connection_nudge import (
    STALE_CONNECTION_AFTER,
    STALE_SENT_KEY,
    find_nudge_targets,
    nudge_eligible_user,
    nudge_markup,
)
from bot.services.winback_survey import resolve_admin_chat_ids
from config.settings import Settings
from db.dal import subscription_dal
from db.database_setup import init_db_connection

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("stale_nudge_test")

TEST_ADMIN = os.environ.get("TEST_ADMIN") == "1"


async def run() -> None:
    settings = Settings()
    session_factory = init_db_connection(settings)
    await load_overrides_from_db(settings, session_factory)
    i18n = get_i18n_instance(path="/app/locales")
    bot = create_telegram_bot(settings)
    try:
        if TEST_ADMIN:
            await send_admin_preview(bot, i18n, settings, session_factory)
        else:
            await dry_run(settings, session_factory)
    finally:
        await bot.session.close()


async def send_admin_preview(bot, i18n, settings, session_factory) -> None:
    async with session_factory() as session:
        chat_ids = await resolve_admin_chat_ids(session, settings)
    logger.info("TEST_ADMIN: %d admin chats", len(chat_ids))
    markup = nudge_markup(i18n, "ru", settings).as_markup()
    texts = [
        i18n.gettext("ru", "stale_connection_notice"),
        i18n.gettext("ru", "stale_connection_notice_trial"),
    ]
    for chat_id in chat_ids:
        for text in texts:
            try:
                await bot.send_message(
                    chat_id, text, parse_mode="HTML", reply_markup=markup
                )
            except Exception:
                logger.exception("  FAILED admin chat %s", chat_id)
            await asyncio.sleep(0.4)
        logger.info("  sent %d variants to admin chat %s", len(texts), chat_id)


async def dry_run(settings, session_factory) -> None:
    now = datetime.now(UTC)
    async with session_factory() as session:
        targets = await find_nudge_targets(session, now)
        logger.info("stale-connection targets: %d", len(targets))
        for sub in targets:
            user = getattr(sub, "user", None)
            notified = await subscription_dal.has_subscription_notification(
                session, int(sub.subscription_id), STALE_SENT_KEY
            )
            quiet_since = sub.last_connected_at or sub.start_date
            logger.info(
                "  sub=%s user=%s tg=%s @%s quiet_since=%s notified=%s eligible=%s",
                sub.subscription_id,
                sub.user_id,
                getattr(user, "telegram_id", None),
                getattr(user, "username", None),
                quiet_since,
                notified,
                nudge_eligible_user(user),
            )
        logger.info("dry run - TEST_ADMIN=1 sends admin preview")


if __name__ == "__main__":
    asyncio.run(run())
