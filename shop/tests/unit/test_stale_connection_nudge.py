"""Stale-connection nudge targeting and markup."""

import unittest
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import patch

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from bot.services import stale_connection_nudge as nudge
from db.base import Base
from db.models import Subscription, User


class StaleConnectionNudgeTargetTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self.factory = async_sessionmaker(self.engine, expire_on_commit=False)
        self.now = datetime.now(UTC)
        self.next_user = 0
        self.next_subscription = 0

    async def asyncTearDown(self) -> None:
        await self.engine.dispose()

    async def _user(self, *, is_banned: bool = False, telegram_id: int | None = None) -> int:
        self.next_user += 1
        user_id = self.next_user
        async with self.factory() as session:
            session.add(
                User(
                    user_id=user_id,
                    is_banned=is_banned,
                    telegram_id=telegram_id if telegram_id is not None else user_id,
                )
            )
            await session.commit()
        return user_id

    async def _subscription(
        self,
        user_id: int,
        *,
        start: datetime | None,
        end: datetime | None,
        provider: str | None = "yookassa",
        status_from_panel: str | None = "ACTIVE",
        is_active: bool = True,
        last_connected_at: datetime | None = None,
    ) -> int:
        self.next_subscription += 1
        sub_id = self.next_subscription
        async with self.factory() as session:
            sub = Subscription(
                user_id=user_id,
                panel_user_uuid=f"panel-user-{sub_id}",
                panel_subscription_uuid=f"panel-sub-{sub_id}",
                start_date=start,
                end_date=end,
                is_active=is_active,
                status_from_panel=status_from_panel,
                provider=provider,
                last_connected_at=last_connected_at,
            )
            session.add(sub)
            await session.commit()
            return int(sub.subscription_id)

    async def _targets(self) -> list[int]:
        async with self.factory() as session:
            subs = await nudge.find_nudge_targets(session, self.now)
            return [int(sub.subscription_id) for sub in subs]

    async def test_paid_subscription_quiet_since_last_connect_is_targeted(self):
        user_id = await self._user()
        sub_id = await self._subscription(
            user_id,
            start=self.now - timedelta(days=10),
            end=self.now + timedelta(days=20),
            last_connected_at=self.now - timedelta(days=5),
        )
        self.assertIn(sub_id, await self._targets())

    async def test_never_connected_paid_subscription_is_targeted_after_grace(self):
        user_id = await self._user()
        sub_id = await self._subscription(
            user_id,
            start=self.now - timedelta(days=5),
            end=self.now + timedelta(days=25),
            last_connected_at=None,
        )
        self.assertIn(sub_id, await self._targets())

    async def test_fresh_paid_subscription_gets_grace_period(self):
        user_id = await self._user()
        sub_id = await self._subscription(
            user_id,
            start=self.now - timedelta(days=1),
            end=self.now + timedelta(days=29),
            last_connected_at=None,
        )
        self.assertNotIn(sub_id, await self._targets())

    async def test_recently_connected_subscription_is_skipped(self):
        user_id = await self._user()
        sub_id = await self._subscription(
            user_id,
            start=self.now - timedelta(days=10),
            end=self.now + timedelta(days=20),
            last_connected_at=self.now - timedelta(hours=2),
        )
        self.assertNotIn(sub_id, await self._targets())

    async def test_trial_provider_is_targeted(self):
        user_id = await self._user()
        sub_id = await self._subscription(
            user_id,
            start=self.now - timedelta(days=3),
            end=self.now + timedelta(days=1),
            provider="trial",
            status_from_panel="TRIAL",
            last_connected_at=None,
        )
        self.assertIn(sub_id, await self._targets())

    async def test_fresh_trial_gets_grace_period(self):
        user_id = await self._user()
        sub_id = await self._subscription(
            user_id,
            start=self.now - timedelta(days=1),
            end=self.now + timedelta(days=2),
            provider="trial",
            status_from_panel="TRIAL",
            last_connected_at=None,
        )
        self.assertNotIn(sub_id, await self._targets())

    async def test_inactive_and_expired_subscriptions_are_skipped(self):
        user_id = await self._user()
        inactive_id = await self._subscription(
            user_id,
            start=self.now - timedelta(days=10),
            end=self.now + timedelta(days=20),
            is_active=False,
            last_connected_at=self.now - timedelta(days=5),
        )
        expired_id = await self._subscription(
            user_id,
            start=self.now - timedelta(days=40),
            end=self.now - timedelta(days=10),
            last_connected_at=self.now - timedelta(days=20),
        )
        targets = await self._targets()
        self.assertNotIn(inactive_id, targets)
        self.assertNotIn(expired_id, targets)

    async def test_banned_user_is_skipped(self):
        user_id = await self._user(is_banned=True)
        sub_id = await self._subscription(
            user_id,
            start=self.now - timedelta(days=10),
            end=self.now + timedelta(days=20),
            last_connected_at=self.now - timedelta(days=5),
        )
        self.assertNotIn(sub_id, await self._targets())


class StaleConnectionNudgeEligibilityTests(unittest.TestCase):
    def test_linked_active_user_is_eligible(self):
        user = SimpleNamespace(
            is_banned=False,
            telegram_id=12345,
            telegram_notifications_status=None,
        )
        self.assertTrue(nudge.nudge_eligible_user(user))

    def test_banned_user_is_not_eligible(self):
        user = SimpleNamespace(
            is_banned=True,
            telegram_id=12345,
            telegram_notifications_status=None,
        )
        self.assertFalse(nudge.nudge_eligible_user(user))

    def test_user_without_telegram_is_not_eligible(self):
        user = SimpleNamespace(
            is_banned=False,
            telegram_id=None,
            telegram_notifications_status=None,
        )
        self.assertFalse(nudge.nudge_eligible_user(user))

    def test_blocked_bot_user_is_not_eligible(self):
        user = SimpleNamespace(
            is_banned=False,
            telegram_id=12345,
            telegram_notifications_status="blocked",
        )
        self.assertFalse(nudge.nudge_eligible_user(user))

    def test_missing_user_is_not_eligible(self):
        self.assertFalse(nudge.nudge_eligible_user(None))


class StaleConnectionNudgeMessageKeyTests(unittest.TestCase):
    def test_trial_subscription_uses_trial_text(self):
        sub = SimpleNamespace(provider="trial", status_from_panel="TRIAL")
        self.assertEqual(
            nudge.nudge_message_key(sub), "stale_connection_notice_trial"
        )

    def test_paid_subscription_uses_paid_text(self):
        sub = SimpleNamespace(provider="yookassa", status_from_panel="ACTIVE")
        self.assertEqual(
            nudge.nudge_message_key(sub), "stale_connection_notice"
        )


class _FakeI18n:
    def gettext(self, lang_code, key, **kwargs):
        return f"<{key}>"


class _FakeSettings(SimpleNamespace):
    pass


class StaleConnectionNudgeMarkupTests(unittest.TestCase):
    def _settings(self) -> _FakeSettings:
        return _FakeSettings(
            SUBSCRIPTION_MINI_APP_URL="https://t.me/ProlivNetworkBot/app",
            support_settings=SimpleNamespace(link="https://t.me/prolivnet?direct"),
        )

    def _button_map(self, markup):
        buttons = {}
        for row in markup.inline_keyboard:
            for button in row:
                buttons[button.text] = button
        return buttons

    def test_markup_contains_connect_support_and_close(self):
        settings = self._settings()
        with patch.object(
            nudge, "bot_install_guide_url", return_value="https://t.me/ProlivNetworkBot/app/install"
        ):
            markup = nudge.nudge_markup(_FakeI18n(), "ru", settings).as_markup()
        buttons = self._button_map(markup)
        connect = buttons["<connect_button>"]
        support = buttons["<stale_connection_support_button>"]
        close = buttons["<stale_connection_close_button>"]
        self.assertIsNotNone(connect.web_app)
        self.assertEqual(
            connect.web_app.url, "https://t.me/ProlivNetworkBot/app/install"
        )
        self.assertEqual(support.url, "https://t.me/prolivnet?direct")
        self.assertEqual(close.callback_data, nudge.CLOSE_CALLBACK)

    def test_connect_button_falls_back_to_mini_app_url(self):
        settings = self._settings()
        with patch.object(nudge, "bot_install_guide_url", return_value=None):
            markup = nudge.nudge_markup(_FakeI18n(), "ru", settings).as_markup()
        buttons = self._button_map(markup)
        self.assertEqual(
            buttons["<connect_button>"].web_app.url,
            "https://t.me/ProlivNetworkBot/app",
        )


if __name__ == "__main__":
    unittest.main()
