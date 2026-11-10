"""Periodic no-trial survey dispatcher.

Every tick finds users registered for at least ``NOTRIAL_MIN_AGE`` who
never got any subscription row (no trial, no paid plan), then sends them
the one-time "why haven't you tried the free period" survey.
"""

import asyncio
import logging
from datetime import UTC, datetime

from aiogram import Bot
from sqlalchemy.orm import sessionmaker

from bot.middlewares.i18n import JsonI18n
from bot.services.notrial_survey import (
    find_survey_targets,
    send_survey_prompt,
    survey_already_sent,
)
from bot.services.winback_survey import survey_eligible_user
from config.settings import Settings

logger = logging.getLogger(__name__)

NOTRIAL_SURVEY_TICK_SECONDS = 1800.0


class NotrialSurveyWorker:
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
                logger.exception("No-trial survey worker tick failed")
            await asyncio.sleep(NOTRIAL_SURVEY_TICK_SECONDS)

    async def _tick(self) -> None:
        if self.bot is None:
            return
        now = datetime.now(UTC)
        async with self.session_factory() as session:
            targets = await find_survey_targets(session, now)
            for user in targets:
                user_id = int(user.user_id)
                if await survey_already_sent(session, user_id):
                    continue
                if not survey_eligible_user(user):
                    continue
                try:
                    await send_survey_prompt(
                        bot=self.bot,
                        i18n=self.i18n,
                        settings=self.settings,
                        session=session,
                        user=user,
                        sent_at=now,
                    )
                except Exception:
                    logger.exception("No-trial survey send failed for user %s", user_id)
            await session.commit()
