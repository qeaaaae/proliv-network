"""Periodic win-back survey dispatcher.

Every tick finds users whose latest subscription expired 24-48h ago and who
still have no active subscription, then sends them the "why did you decide
not to renew" survey once per lapsed subscription row.
"""

import asyncio
import logging
from datetime import UTC, datetime

from aiogram import Bot
from sqlalchemy.orm import sessionmaker

from bot.middlewares.i18n import JsonI18n
from bot.services.winback_survey import (
    WINBACK_SENT_KEY,
    find_survey_targets,
    send_survey_prompt,
    survey_eligible_user,
)
from config.settings import Settings
from db.dal import subscription_dal

logger = logging.getLogger(__name__)

WINBACK_SURVEY_TICK_SECONDS = 1800.0


class WinbackSurveyWorker:
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
                logger.exception("Win-back survey worker tick failed")
            await asyncio.sleep(WINBACK_SURVEY_TICK_SECONDS)

    async def _tick(self) -> None:
        if self.bot is None:
            return
        now = datetime.now(UTC)
        async with self.session_factory() as session:
            targets = await find_survey_targets(session, now)
            for sub in targets:
                subscription_id = int(sub.subscription_id)
                if await subscription_dal.has_subscription_notification(
                    session, subscription_id, WINBACK_SENT_KEY
                ):
                    continue
                user = getattr(sub, "user", None)
                if not survey_eligible_user(user):
                    continue
                try:
                    await send_survey_prompt(
                        bot=self.bot,
                        i18n=self.i18n,
                        settings=self.settings,
                        session=session,
                        sub=sub,
                        sent_at=now,
                    )
                except Exception:
                    logger.exception(
                        "Win-back survey send failed for subscription %s",
                        subscription_id,
                    )
            await session.commit()
