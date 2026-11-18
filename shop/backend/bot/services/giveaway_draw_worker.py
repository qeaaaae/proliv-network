"""Worker loop that reminds the admin before a scheduled giveaway draw.

One hour before ``scheduled_draw_at`` the composing admin gets a private
reminder. The draw itself is always manual - the admin picks winners via
the admin card and announces the results himself; nothing is posted to
the group automatically.
"""

import asyncio
import logging
from datetime import UTC, datetime, timedelta, timezone

from aiogram import Bot
from sqlalchemy.orm import sessionmaker

from bot.middlewares.i18n import JsonI18n
from config.settings import Settings
from db.dal import giveaway_dal

logger = logging.getLogger(__name__)

GIVEAWAY_DRAW_WORKER_INTERVAL_SECONDS = 30.0
GIVEAWAY_REMINDER_WINDOW = timedelta(hours=1)
_MSK = timezone(timedelta(hours=3))


class GiveawayDrawWorker:
    def __init__(
        self,
        settings: Settings,
        session_factory: sessionmaker,
        i18n: JsonI18n,
        bot: Bot | None,
    ) -> None:
        self.settings = settings
        self.session_factory = session_factory
        self.i18n = i18n
        self.bot = bot

    async def run(self) -> None:
        while True:
            try:
                await self._tick()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Giveaway draw worker tick failed")
            await asyncio.sleep(GIVEAWAY_DRAW_WORKER_INTERVAL_SECONDS)

    async def _tick(self) -> None:
        now = datetime.now(UTC)
        async with self.session_factory() as session:
            pending = await giveaway_dal.giveaways_pending_reminder(
                session, now, GIVEAWAY_REMINDER_WINDOW
            )
            reminders = [
                (
                    int(g.giveaway_id),
                    int(g.created_by_telegram_id) if g.created_by_telegram_id else None,
                    g.scheduled_draw_at,
                )
                for g in pending
            ]
            for giveaway in pending:
                await giveaway_dal.mark_reminder_sent(session, giveaway)
            await session.commit()
        for giveaway_id, admin_id, when in reminders:
            try:
                await self._send_reminder(giveaway_id, admin_id, when)
            except Exception:
                logger.exception("Giveaway %s reminder failed", giveaway_id)

    async def _send_reminder(self, giveaway_id: int, admin_id: int | None, when) -> None:
        if self.bot is None or not admin_id:
            return
        lang = self.settings.DEFAULT_LANGUAGE
        _ = lambda key, **kwargs: self.i18n.gettext(lang, key, **kwargs)
        when_msk = when.astimezone(_MSK).strftime("%d.%m.%Y %H:%M") if when else ""
        await self.bot.send_message(
            chat_id=admin_id,
            text=_(
                "admin_giveaway_reminder_text",
                giveaway_id=giveaway_id,
                when=when_msk,
            ),
            parse_mode="HTML",
        )
