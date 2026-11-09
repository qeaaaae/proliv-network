"""Worker loop that draws scheduled giveaways when their time comes.

An active giveaway with ``scheduled_draw_at`` in the past is drawn exactly
like the manual admin draw: winners are picked with fresh condition checks,
the giveaway is finished, results are announced in the group as a reply to
the post, and the composing admin gets the winner list in PM.
"""

import asyncio
import logging
from datetime import UTC, datetime

from aiogram import Bot
from sqlalchemy.orm import sessionmaker

from bot.middlewares.i18n import JsonI18n
from bot.services.giveaway_service import draw_giveaway_winners, participant_label
from bot.services.subscription_service_impl.core import SubscriptionService
from config.settings import Settings
from db.dal import giveaway_dal
from db.giveaway_models import GIVEAWAY_STATUS_ACTIVE

logger = logging.getLogger(__name__)

GIVEAWAY_DRAW_WORKER_INTERVAL_SECONDS = 30.0


class GiveawayDrawWorker:
    def __init__(
        self,
        settings: Settings,
        session_factory: sessionmaker,
        subscription_service: SubscriptionService,
        i18n: JsonI18n,
        bot: Bot | None,
    ) -> None:
        self.settings = settings
        self.session_factory = session_factory
        self.subscription_service = subscription_service
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
        async with self.session_factory() as session:
            due = await giveaway_dal.due_giveaways(session, datetime.now(UTC))
        for giveaway in due:
            try:
                await self._draw_one(int(giveaway.giveaway_id))
            except Exception:
                logger.exception("Scheduled draw for giveaway %s failed", giveaway.giveaway_id)

    async def _draw_one(self, giveaway_id: int) -> None:
        lang = self.settings.DEFAULT_LANGUAGE
        _ = lambda key, **kwargs: self.i18n.gettext(lang, key, **kwargs)

        async with self.session_factory() as session:
            giveaway = await giveaway_dal.get_giveaway(session, giveaway_id)
            if giveaway is None or giveaway.status != GIVEAWAY_STATUS_ACTIVE:
                return
            winners = await draw_giveaway_winners(session, giveaway)
            await giveaway_dal.finish_giveaway(session, giveaway)
            await session.commit()

        winners_lines = [
            _("admin_giveaway_winner_row", place=place, user=participant_label(user))
            for place, user in winners
        ]
        winners_block = (
            "\n".join(winners_lines) if winners_lines else _("admin_giveaway_no_winners")
        )

        if self.bot is None:
            return

        if giveaway.chat_id:
            try:
                await self.bot.send_message(
                    chat_id=int(giveaway.chat_id),
                    text=_("admin_giveaway_group_results", winners=winners_block),
                    parse_mode="HTML",
                    reply_to_message_id=(int(giveaway.message_id) if giveaway.message_id else None),
                    allow_sending_without_reply=True,
                )
            except Exception as e:
                logger.warning("Scheduled giveaway %s group announce failed: %s", giveaway_id, e)

        if giveaway.created_by_telegram_id:
            try:
                await self.bot.send_message(
                    chat_id=int(giveaway.created_by_telegram_id),
                    text=_(
                        "admin_giveaway_results_text",
                        giveaway_id=giveaway_id,
                        winners=winners_block,
                    ),
                    parse_mode="HTML",
                )
            except Exception as e:
                logger.warning("Scheduled giveaway %s admin notify failed: %s", giveaway_id, e)
