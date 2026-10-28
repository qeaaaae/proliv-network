from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

from bot.services.telegram_account import (
    TelegramAccountRequiredError,
    require_telegram_account_id,
    resolve_telegram_account_id,
)


class TelegramAccountResolutionTests(IsolatedAsyncioTestCase):
    async def test_transport_and_account_ids_remain_distinct(self):
        session = object()
        with patch(
            "bot.services.telegram_account.user_dal.get_user_by_telegram_id",
            new_callable=AsyncMock,
            return_value=SimpleNamespace(user_id=1_000_000_000_001),
        ) as lookup:
            self.assertEqual(
                await require_telegram_account_id(session, 123456789), 1_000_000_000_001
            )
        lookup.assert_awaited_once_with(session, 123456789)

    async def test_unlinked_id_cannot_access_a_same_number_account(self):
        with (
            patch(
                "bot.services.telegram_account.user_dal.get_user_by_telegram_id",
                new_callable=AsyncMock,
                return_value=None,
            ),
            self.assertRaises(TelegramAccountRequiredError),
        ):
            await require_telegram_account_id(object(), 123456789)

    async def test_resolve_returns_account_id_for_linked_telegram_id(self):
        session = object()
        with patch(
            "bot.services.telegram_account.user_dal.get_user_by_telegram_id",
            new_callable=AsyncMock,
            return_value=SimpleNamespace(user_id=1_000_000_000_001),
        ) as lookup:
            self.assertEqual(
                await resolve_telegram_account_id(session, 123456789), 1_000_000_000_001
            )
        lookup.assert_awaited_once_with(session, 123456789)

    async def test_resolve_returns_none_for_unlinked_telegram_id(self):
        with patch(
            "bot.services.telegram_account.user_dal.get_user_by_telegram_id",
            new_callable=AsyncMock,
            return_value=None,
        ):
            self.assertIsNone(await resolve_telegram_account_id(object(), 123456789))
