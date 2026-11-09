import unittest
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock, patch

from aiogram import Bot, types

from bot.handlers.admin import giveaway as giveaway_module
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


class GiveawayTextStepTest(unittest.IsolatedAsyncioTestCase):
    async def test_text_goes_to_image_step(self):
        state = _state()
        message = SimpleNamespace(
            html_text="draw <tg-emoji emoji-id='1'>🔥</tg-emoji>",
            photo=None,
            answer=AsyncMock(),
        )
        await giveaway_module.process_giveaway_text_handler(
            cast(types.Message, message), state, _i18n_data(), settings_stub(), _session()
        )
        state.update_data.assert_awaited_once_with(
            giveaway_html="draw <tg-emoji emoji-id='1'>🔥</tg-emoji>"
        )
        state.set_state.assert_awaited_once()

    async def test_photo_with_caption_goes_to_schedule_step(self):
        state = _state()
        message = SimpleNamespace(
            html_text="caption",
            photo=[SimpleNamespace(file_id="small"), SimpleNamespace(file_id="big")],
            answer=AsyncMock(),
            chat=SimpleNamespace(id=42),
        )
        await giveaway_module.process_giveaway_text_handler(
            cast(types.Message, message),
            state,
            _i18n_data(),
            settings_stub(),
            _session(),
        )
        state.update_data.assert_any_await(giveaway_file_id="big")
        state.set_state.assert_awaited_once()

    async def test_schedule_step_creates_draft_and_confirms(self):
        state = _state({"giveaway_html": "hi"})
        message = SimpleNamespace(
            text="08.11.2026 20:00", answer=AsyncMock(), chat=SimpleNamespace(id=42)
        )
        draft = SimpleNamespace(giveaway_id=7)
        with patch.object(
            giveaway_module.giveaway_dal, "create_giveaway", AsyncMock(return_value=draft)
        ) as create:
            await giveaway_module.process_giveaway_schedule_handler(
                cast(types.Message, message),
                state,
                _i18n_data(),
                settings_stub(),
                _session(),
            )
        create.assert_awaited_once()
        self.assertIsNotNone(create.await_args.kwargs["scheduled_draw_at"])
        state.update_data.assert_any_await(giveaway_id=7)

    async def test_empty_message_asks_for_text(self):
        state = _state()
        message = SimpleNamespace(html_text="  ", photo=None, answer=AsyncMock())
        await giveaway_module.process_giveaway_text_handler(
            cast(types.Message, message), state, _i18n_data(), settings_stub(), _session()
        )
        message.answer.assert_awaited_once()
        state.update_data.assert_not_awaited()


class DeliverGiveawayTest(unittest.IsolatedAsyncioTestCase):
    async def test_text_post_with_participate_button(self):
        bot = SimpleNamespace(
            send_message=AsyncMock(return_value=SimpleNamespace(message_id=10)),
            send_photo=AsyncMock(),
        )
        await giveaway_module._deliver_giveaway(
            cast(Bot, bot),
            -100555,
            {"giveaway_html": "<b>hi</b>"},
            "https://t.me/bot?start=giveaway_7",
            "Join",
        )
        kwargs = bot.send_message.await_args.kwargs
        self.assertEqual(kwargs["chat_id"], -100555)
        markup = cast(types.InlineKeyboardMarkup, kwargs["reply_markup"])
        self.assertEqual(markup.inline_keyboard[0][0].url, "https://t.me/bot?start=giveaway_7")

    async def test_photo_post_without_url_has_no_markup(self):
        bot = SimpleNamespace(
            send_message=AsyncMock(),
            send_photo=AsyncMock(return_value=SimpleNamespace(message_id=11)),
        )
        await giveaway_module._deliver_giveaway(
            cast(Bot, bot),
            1,
            {"giveaway_html": "cap", "giveaway_file_id": "fid"},
            None,
            "Join",
        )
        kwargs = bot.send_photo.await_args.kwargs
        self.assertEqual(kwargs["photo"], "fid")
        self.assertIsNone(kwargs["reply_markup"])


class GiveawaySendTest(unittest.IsolatedAsyncioTestCase):
    def _callback(self, data: str, chat_id: int = 42) -> Any:
        return SimpleNamespace(
            data=data,
            message=SimpleNamespace(
                chat=SimpleNamespace(id=chat_id), answer=AsyncMock(), edit_text=AsyncMock()
            ),
            answer=AsyncMock(),
            from_user=SimpleNamespace(id=42),
        )

    async def test_group_send_publishes_giveaway(self):
        state = _state({"giveaway_id": 7, "giveaway_html": "hi"})
        callback = self._callback("admin_giveaway:send_group", chat_id=42)
        session = _session()
        giveaway = SimpleNamespace(giveaway_id=7, status="draft")
        bot = SimpleNamespace(
            get_me=AsyncMock(return_value=SimpleNamespace(username="proliv_bot")),
            send_message=AsyncMock(return_value=SimpleNamespace(message_id=99)),
            send_photo=AsyncMock(),
        )
        with (
            patch.object(
                giveaway_module.giveaway_dal,
                "get_giveaway",
                AsyncMock(return_value=giveaway),
            ),
            patch.object(giveaway_module.giveaway_dal, "publish_giveaway", AsyncMock()) as publish,
        ):
            await giveaway_module.giveaway_send_handler(
                cast(types.CallbackQuery, callback),
                state,
                _i18n_data(),
                settings_stub(ADMIN_POST_CHAT_ID=-100555),
                session,
                cast(Bot, bot),
            )
        self.assertEqual(bot.send_message.await_args.kwargs["chat_id"], -100555)
        publish.assert_awaited_once()
        self.assertEqual(publish.await_args.kwargs["message_id"], 99)
        session.commit.assert_awaited_once()
        state.clear.assert_awaited_once()

    async def test_test_send_keeps_draft(self):
        state = _state({"giveaway_id": 7, "giveaway_html": "hi"})
        callback = self._callback("admin_giveaway:send_test", chat_id=42)
        session = _session()
        giveaway = SimpleNamespace(giveaway_id=7, status="draft")
        bot = SimpleNamespace(
            get_me=AsyncMock(return_value=SimpleNamespace(username="proliv_bot")),
            send_message=AsyncMock(return_value=SimpleNamespace(message_id=99)),
            send_photo=AsyncMock(),
        )
        with (
            patch.object(
                giveaway_module.giveaway_dal,
                "get_giveaway",
                AsyncMock(return_value=giveaway),
            ),
            patch.object(giveaway_module.giveaway_dal, "publish_giveaway", AsyncMock()) as publish,
        ):
            await giveaway_module.giveaway_send_handler(
                cast(types.CallbackQuery, callback),
                state,
                _i18n_data(),
                settings_stub(ADMIN_POST_CHAT_ID=-100555),
                session,
                cast(Bot, bot),
            )
        self.assertEqual(bot.send_message.await_args.kwargs["chat_id"], 42)
        publish.assert_not_awaited()
        state.clear.assert_not_awaited()


class DrawWinnersTest(unittest.IsolatedAsyncioTestCase):
    async def test_draw_skips_ineligible_and_marks_places(self):
        users = [
            SimpleNamespace(user_id=1, is_banned=False),
            SimpleNamespace(user_id=2, is_banned=True),
            SimpleNamespace(user_id=3, is_banned=False),
        ]
        participants = [SimpleNamespace(place=None) for _ in users]
        rows = list(zip(participants, users, strict=True))
        giveaway = SimpleNamespace(giveaway_id=7, winners_count=1)
        set_place = AsyncMock()
        from bot.services import giveaway_service

        with (
            patch.object(
                giveaway_service.giveaway_dal,
                "participant_users",
                AsyncMock(return_value=rows),
            ),
            patch.object(giveaway_service.giveaway_dal, "set_participant_place", set_place),
        ):
            winners = await giveaway_service.draw_giveaway_winners(
                _session(), giveaway
            )
        self.assertEqual(len(winners), 1)
        place, user = winners[0]
        self.assertEqual(place, 1)
        self.assertFalse(user.is_banned)
        set_place.assert_awaited_once()


class GiveawayScheduleParseTest(unittest.TestCase):
    _NOW = giveaway_module.datetime(2026, 11, 4, 12, 0, tzinfo=giveaway_module.UTC)

    def test_parses_date_and_time_msk(self):
        when = giveaway_module.parse_giveaway_schedule("08.11 20:00", now=self._NOW)
        self.assertIsNotNone(when)
        self.assertEqual(when.astimezone(giveaway_module.UTC).hour, 17)

    def test_parses_full_year(self):
        when = giveaway_module.parse_giveaway_schedule("08.11.2026 20:30", now=self._NOW)
        self.assertIsNotNone(when)
        self.assertEqual(when.astimezone(giveaway_module.UTC).hour, 17)

    def test_rejects_past_and_garbage(self):
        self.assertIsNone(giveaway_module.parse_giveaway_schedule("01.11 20:00", now=self._NOW))
        self.assertIsNone(giveaway_module.parse_giveaway_schedule("hello", now=self._NOW))
        self.assertIsNone(giveaway_module.parse_giveaway_schedule("32.13 99:99", now=self._NOW))


if __name__ == "__main__":
    unittest.main()
