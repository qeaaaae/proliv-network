"""Periodic stale-connection nudge dispatcher.

Every tick finds users on an active subscription (paid or trial) who have
not connected for a few days and sends them the "something not working?"
help message once per subscription row.
"""

import asyncio
import logging
from datetime import UTC, datetime

from aiogram import Bot
from sqlalchemy.orm import sessionmaker

from bot.middlewares.i18n import JsonI18n
from bot.services.stale_connection_nudge import (
    STALE_SENT_KEY,
    find_nudge_targets,
    nudge_eligible_user,
    send_nudge,
)
from config.settings import Settings
from db.dal import subscription_dal

logger = logging.getLogger(__name__)

STALE_NUDGE_TICK_SECONDS = 3600.0


class StaleConnectionNudgeWorker:
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
                logger.exception("Stale-connection nudge worker tick failed")
            await asyncio.sleep(STALE_NUDGE_TICK_SECONDS)

    async def _tick(self) -> None:
        if self.bot is None:
            return
        now = datetime.now(UTC)
        async with self.session_factory() as session:
            targets = await find_nudge_targets(session, now)
            for sub in targets:
                subscription_id = int(sub.subscription_id)
                if await subscription_dal.has_subscription_notification(
                    session, subscription_id, STALE_SENT_KEY
                ):
                    continue
                user = getattr(sub, "user", None)
                if not nudge_eligible_user(user):
                    continue
                try:
                    await send_nudge(
                        bot=self.bot,
                        i18n=self.i18n,
                        settings=self.settings,
                        session=session,
                        sub=sub,
                        sent_at=now,
                    )
                except Exception:
                    logger.exception(
                        "Stale-connection nudge send failed for subscription %s",
                        subscription_id,
                    )
            await session.commit()
