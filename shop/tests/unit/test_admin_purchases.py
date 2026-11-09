import unittest
from datetime import UTC, date, datetime
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock, patch

from aiogram import types

from bot.handlers.admin import purchases as purchases_module
from bot.services import purchase_reminder_worker as worker_module
from bot.states.admin_states import AdminStates
from tests.support.settings_stub import settings_stub


def _i18n_data() -> dict:
    return {
        "current_language": "ru",
        "i18n_instance": SimpleNamespace(
            gettext=lambda lang, key, **kwargs: f"{key}:{kwargs}" if kwargs else key
        ),
    }


def _state(data: dict | None = None) -> Any:
    store = dict(data or {})
    state = SimpleNamespace(
        set_state=AsyncMock(),
        clear=AsyncMock(side_effect=store.clear),
    )
    state.update_data = AsyncMock(side_effect=lambda **kwargs: store.update(kwargs))
    state.get_data = AsyncMock(side_effect=lambda: dict(store))
    return state


def _session() -> Any:
    return SimpleNamespace(commit=AsyncMock(), rollback=AsyncMock())


class PurchaseDateParseTest(unittest.TestCase):
    _NOW = datetime(2026, 11, 8, 12, 0, tzinfo=UTC)  # 15:00 MSK

    def test_parses_full_and_short_dates(self):
        self.assertEqual(
            purchases_module.parse_purchase_date("01.11.2026", now=self._NOW),
            date(2026, 11, 1),
        )
        self.assertEqual(
            purchases_module.parse_purchase_date("01.11.26", now=self._NOW),
            date(2026, 11, 1),
        )
        self.assertEqual(
            purchases_module.parse_purchase_date("01.11", now=self._NOW),
            date(2026, 11, 1),
        )

    def test_today_word(self):
        self.assertEqual(
            purchases_module.parse_purchase_date("сегодня", now=self._NOW),
            date(2026, 11, 8),
        )
        self.assertEqual(
            purchases_module.parse_purchase_date("today", now=self._NOW),
            date(2026, 11, 8),
        )

    def test_rejects_future_and_garbage(self):
        self.assertIsNone(purchases_module.parse_purchase_date("09.11", now=self._NOW))
        self.assertIsNone(purchases_module.parse_purchase_date("32.13.2026", now=self._NOW))
        self.assertIsNone(purchases_module.parse_purchase_date("hello", now=self._NOW))
        self.assertIsNone(purchases_module.parse_purchase_date("", now=self._NOW))


class PurchasePeriodParseTest(unittest.TestCase):
    def test_units(self):
        self.assertEqual(purchases_module.parse_purchase_period("30"), (30, "days"))
        self.assertEqual(purchases_module.parse_purchase_period("45 дней"), (45, "days"))
        self.assertEqual(purchases_module.parse_purchase_period("2 недели"), (2, "weeks"))
        self.assertEqual(purchases_module.parse_purchase_period("6 месяцев"), (6, "months"))
        self.assertEqual(purchases_module.parse_purchase_period("1 год"), (1, "years"))
        self.assertEqual(purchases_module.parse_purchase_period("3 months"), (3, "months"))

    def test_rejects_bad_input(self):
        self.assertIsNone(purchases_module.parse_purchase_period("0 дней"))
        self.assertIsNone(purchases_module.parse_purchase_period("месяц"))
        self.assertIsNone(purchases_module.parse_purchase_period("5 штук"))
        self.assertIsNone(purchases_module.parse_purchase_period(""))


class PriceAmountParseTest(unittest.TestCase):
    def test_ruble_labels(self):
        self.assertEqual(purchases_module.parse_price_amount("430 ₽/мес"), 430.0)
        self.assertEqual(purchases_module.parse_price_amount("1 620 ₽/год"), 1620.0)
        self.assertEqual(purchases_module.parse_price_amount("270"), 270.0)
        self.assertEqual(purchases_module.parse_price_amount("150,5 руб"), 150.5)

    def test_skips_foreign_and_empty(self):
        self.assertIsNone(purchases_module.parse_price_amount("$5/yr"))
        self.assertIsNone(purchases_module.parse_price_amount("5 €"))
        self.assertIsNone(purchases_module.parse_price_amount(""))
        self.assertIsNone(purchases_module.parse_price_amount(None))
        self.assertIsNone(purchases_module.parse_price_amount("бесплатно"))


class ComputeExpiryTest(unittest.TestCase):
    def test_days_and_weeks(self):
        start = date(2026, 11, 8)
        self.assertEqual(purchases_module.compute_expiry(start, 30, "days"), date(2026, 12, 8))
        self.assertEqual(purchases_module.compute_expiry(start, 2, "weeks"), date(2026, 11, 22))

    def test_months_and_years_calendar(self):
        start = date(2026, 11, 8)
        self.assertEqual(purchases_module.compute_expiry(start, 1, "months"), date(2026, 12, 8))
        self.assertEqual(purchases_module.compute_expiry(start, 1, "years"), date(2027, 11, 8))

    def test_month_end_clamps(self):
        start = date(2026, 1, 31)
        self.assertEqual(purchases_module.compute_expiry(start, 1, "months"), date(2026, 2, 28))


class PurchaseComposerStepsTest(unittest.IsolatedAsyncioTestCase):
    async def test_provider_step_moves_to_title(self):
        state = _state()
        message = SimpleNamespace(text="Aeza", answer=AsyncMock())
        await purchases_module.process_purchase_provider_handler(
            cast(types.Message, message), state, _i18n_data(), settings_stub()
        )
        state.update_data.assert_awaited_once_with(purchase_provider="Aeza")
        state.set_state.assert_awaited_once_with(AdminStates.waiting_for_purchase_title)

    async def test_title_step_moves_to_price(self):
        state = _state()
        message = SimpleNamespace(text="VPS-0", answer=AsyncMock())
        await purchases_module.process_purchase_title_handler(
            cast(types.Message, message), state, _i18n_data(), settings_stub()
        )
        state.update_data.assert_awaited_once_with(purchase_title="VPS-0")
        state.set_state.assert_awaited_once_with(AdminStates.waiting_for_purchase_price)

    async def test_price_step_moves_to_note(self):
        state = _state()
        message = SimpleNamespace(text="430 ₽/мес", answer=AsyncMock())
        await purchases_module.process_purchase_price_handler(
            cast(types.Message, message), state, _i18n_data(), settings_stub()
        )
        state.update_data.assert_awaited_once_with(purchase_price_label="430 ₽/мес")
        state.set_state.assert_awaited_once_with(AdminStates.waiting_for_purchase_note)

    async def test_price_skip_moves_to_note(self):
        state = _state()
        callback = SimpleNamespace(
            data="admin_purchases:skip_price",
            message=SimpleNamespace(answer=AsyncMock(), edit_text=AsyncMock()),
            answer=AsyncMock(),
            from_user=SimpleNamespace(id=42),
        )
        await purchases_module.skip_purchase_price_handler(
            cast(types.CallbackQuery, callback), state, _i18n_data(), settings_stub()
        )
        state.update_data.assert_awaited_once_with(purchase_price_label=None)
        state.set_state.assert_awaited_once_with(AdminStates.waiting_for_purchase_note)

    async def test_paid_on_step_moves_to_period(self):
        state = _state()
        message = SimpleNamespace(text="сегодня", answer=AsyncMock())
        await purchases_module.process_purchase_paid_on_handler(
            cast(types.Message, message), state, _i18n_data(), settings_stub()
        )
        state.set_state.assert_awaited_once_with(AdminStates.waiting_for_purchase_period)

    async def test_period_step_shows_preview(self):
        state = _state(
            {
                "purchase_provider": "Aeza",
                "purchase_title": "VPS-0",
                "purchase_paid_on": "2026-11-08",
            }
        )
        message = SimpleNamespace(text="1 месяц", answer=AsyncMock())
        await purchases_module.process_purchase_period_handler(
            cast(types.Message, message), state, _i18n_data(), settings_stub()
        )
        state.set_state.assert_awaited_once_with(AdminStates.confirming_purchase)
        message.answer.assert_awaited_once()

    async def test_save_creates_row_and_renders_list(self):
        state = _state(
            {
                "purchase_provider": "Aeza",
                "purchase_title": "VPS-0",
                "purchase_note": None,
                "purchase_price_label": "430 ₽/мес",
                "purchase_paid_on": "2026-11-08",
                "purchase_period_label": "1 месяц",
            }
        )
        callback = SimpleNamespace(
            data="admin_purchases:save",
            message=SimpleNamespace(
                chat=SimpleNamespace(id=42), edit_text=AsyncMock(), answer=AsyncMock()
            ),
            answer=AsyncMock(),
            from_user=SimpleNamespace(id=42),
        )
        session = _session()
        created = SimpleNamespace(
            purchase_id=7,
            provider="Aeza",
            title="VPS-0",
            note=None,
            price_label="430 ₽/мес",
            paid_on=date(2026, 11, 8),
            period_label="1 месяц",
            expires_on=date(2026, 12, 8),
        )
        with (
            patch.object(
                purchases_module.admin_purchase_dal,
                "create_purchase",
                AsyncMock(return_value=created),
            ) as create,
            patch.object(
                purchases_module.admin_purchase_dal,
                "count_purchases",
                AsyncMock(return_value=1),
            ),
            patch.object(
                purchases_module.admin_purchase_dal,
                "list_purchases",
                AsyncMock(return_value=[created]),
            ),
            patch.object(
                purchases_module.admin_purchase_dal,
                "all_expiry_price_pairs",
                AsyncMock(return_value=[(date(2026, 12, 8), "430 ₽/мес")]),
            ),
        ):
            await purchases_module.purchase_save_handler(
                cast(types.CallbackQuery, callback),
                state,
                _i18n_data(),
                settings_stub(),
                session,
            )
        kwargs = create.await_args.kwargs
        self.assertEqual(kwargs["expires_on"], date(2026, 12, 8))
        self.assertEqual(kwargs["provider"], "Aeza")
        self.assertEqual(kwargs["price_label"], "430 ₽/мес")
        session.commit.assert_awaited_once()
        state.clear.assert_awaited_once()


class ReminderWorkerTest(unittest.IsolatedAsyncioTestCase):
    async def test_reminder_days_left_mapping(self):
        worker = worker_module.PurchaseReminderWorker(
            settings=settings_stub(DEFAULT_LANGUAGE="ru"),
            session_factory=SimpleNamespace(),
            i18n=SimpleNamespace(
                gettext=lambda lang, key, **kwargs: f"{key}:{kwargs}" if kwargs else key
            ),
            bot=None,
        )
        sends: list[dict] = []

        class _QM:
            async def send_message(self, **kwargs):
                sends.append(kwargs)

        purchase = SimpleNamespace(
            purchase_id=1,
            title="VPS-0",
            provider="Aeza",
            note=None,
            price_label="430 ₽/мес",
            expires_on=date(2026, 11, 8),
        )
        with patch.object(worker_module, "get_queue_manager", return_value=_QM()):
            delivered = await worker._notify_admins([42], purchase, 3)
        self.assertTrue(delivered)
        self.assertIn("admin_purchases_reminder_days", sends[0]["text"])
        self.assertEqual(sends[0]["chat_id"], 42)


if __name__ == "__main__":
    unittest.main()
