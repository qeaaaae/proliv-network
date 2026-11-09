"""Daily reminder loop for admin purchase expirations.

Once a day at 10:00 Moscow time (fixed UTC+3) the worker PMs every admin
about purchases whose ``expires_on`` falls on a reminder day: 3 and 2 days
before expiry, on the expiry day itself, and once the day after when the
payment is already overdue. ``last_notified_on`` on the row makes sends
idempotent across worker restarts; renewing the purchase resets it.
"""

import asyncio
import logging
from datetime import UTC, date, datetime, timedelta, timezone
from html import escape

from aiogram import Bot
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from bot.middlewares.i18n import JsonI18n
from bot.utils.message_queue import get_queue_manager
from config.settings import Settings
from db.admin_purchase_models import AdminPurchase
from db.auth_models import AccountRole
from db.dal import admin_purchase_dal
from db.models import User

logger = logging.getLogger(__name__)

PURCHASE_REMINDER_TICK_SECONDS = 60.0
PURCHASE_REMINDER_TZ = timezone(timedelta(hours=3))
PURCHASE_REMINDER_HOUR = 10
# days_left values that trigger a PM: 3/2 days before, the expiry day, day after.
PURCHASE_REMINDER_DAYS_LEFT = (3, 2, 0, -1)


class PurchaseReminderWorker:
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
        last_run: date | None = None
        while True:
            try:
                now_local = datetime.now(UTC).astimezone(PURCHASE_REMINDER_TZ)
                today = now_local.date()
                if now_local.hour >= PURCHASE_REMINDER_HOUR and last_run != today:
                    await self._tick(today)
                    last_run = today
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Purchase reminder worker tick failed")
            await asyncio.sleep(PURCHASE_REMINDER_TICK_SECONDS)

    async def _tick(self, today: date) -> None:
        if self.bot is None:
            logger.warning("Purchase reminder pass skipped: bot is unavailable")
            return
        async with self.session_factory() as session:
            due = await admin_purchase_dal.purchases_due_for_reminder(
                session, today, PURCHASE_REMINDER_DAYS_LEFT
            )
            if not due:
                return
            admin_chat_ids = await self._admin_chat_ids(session)
            if not admin_chat_ids:
                logger.warning("Purchase reminder skipped: no admin chat ids resolved")
                return
            for purchase in due:
                days_left = (purchase.expires_on - today).days
                delivered = await self._notify_admins(admin_chat_ids, purchase, days_left)
                if delivered:
                    await admin_purchase_dal.mark_notified(session, purchase, today)
            await session.commit()

    async def _admin_chat_ids(self, session: AsyncSession) -> list[int]:
        """Telegram chat ids of owner/admin accounts plus raw ADMIN_IDS."""
        chat_ids: set[int] = set()
        result = await session.execute(
            select(User.telegram_id)
            .join(AccountRole, AccountRole.user_id == User.user_id)
            .where(
                AccountRole.role.in_(("owner", "admin")),
                AccountRole.revoked_at.is_(None),
                User.telegram_id.is_not(None),
                User.is_banned.is_(False),
            )
            .distinct()
        )
        for telegram_id in result.scalars().all():
            if telegram_id is not None:
                chat_ids.add(int(telegram_id))
        for admin_id in self.settings.ADMIN_IDS:
            chat_ids.add(int(admin_id))
        return sorted(chat_ids)

    async def _notify_admins(
        self, chat_ids: list[int], purchase: AdminPurchase, days_left: int
    ) -> bool:
        lang = self.settings.DEFAULT_LANGUAGE
        _ = lambda key, **kwargs: self.i18n.gettext(lang, key, **kwargs)
        if days_left > 0:
            days_line = _("admin_purchases_reminder_days", days=days_left)
        elif days_left == 0:
            days_line = _("admin_purchases_reminder_today")
        else:
            days_line = _("admin_purchases_reminder_overdue", days=-days_left)
        note_line = (
            _("admin_purchases_reminder_note", note=escape(str(purchase.note)))
            if purchase.note
            else ""
        )
        price_line = (
            _("admin_purchases_reminder_price", price=escape(str(purchase.price_label)))
            if purchase.price_label
            else ""
        )
        text = _(
            "admin_purchases_reminder",
            title=escape(str(purchase.title)),
            provider=escape(str(purchase.provider)),
            price=price_line,
            note=note_line,
            expires_on=purchase.expires_on.strftime("%d.%m.%Y"),
            days=days_line,
        )
        queue_manager = get_queue_manager()
        delivered = False
        for chat_id in chat_ids:
            try:
                if queue_manager is not None:
                    await queue_manager.send_message(chat_id=chat_id, text=text, parse_mode="HTML")
                else:
                    assert self.bot is not None  # guarded by _tick
                    await self.bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")
                delivered = True
            except Exception as e:
                logger.warning(
                    "Purchase %s reminder to admin %s failed: %s",
                    purchase.purchase_id,
                    chat_id,
                    e,
                )
        return delivered
