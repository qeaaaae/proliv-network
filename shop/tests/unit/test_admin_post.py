import unittest
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock, patch

from aiogram import Bot, types

from bot.handlers.admin import post as post_module
from tests.support.settings_stub import settings_stub


def _i18n_data() -> dict:
    return {
        "current_language": "ru",
        "i18n_instance": SimpleNamespace(
            gettext=lambda lang, key, **kwargs: f"{key}:{kwargs}" if kwargs else key
        ),
    }


def _state(data: dict | None = None) -> Any:
    state = SimpleNamespace(
        update_data=AsyncMock(),
        set_state=AsyncMock(),
        clear=AsyncMock(),
        get_data=AsyncMock(return_value=data or {}),
    )
    return state


class PostButtonUrlTest(unittest.TestCase):
    def test_accepts_https_url(self):
        self.assertEqual(
            post_module.normalize_post_button_url("https://example.com/page"),
            "https://example.com/page",
        )

    def test_prepends_https_for_bare_domain(self):
        self.assertEqual(
            post_module.normalize_post_button_url("t.me/proliv"),
            "https://t.me/proliv",
        )

    def test_accepts_tg_scheme(self):
        self.assertEqual(
            post_module.normalize_post_button_url("tg://resolve?domain=x"),
            "tg://resolve?domain=x",
        )

    def test_rejects_non_url_and_bad_schemes(self):
        self.assertIsNone(post_module.normalize_post_button_url(""))
        self.assertIsNone(post_module.normalize_post_button_url("просто текст"))
        self.assertIsNone(post_module.normalize_post_button_url("ftp://example.com"))
        self.assertIsNone(post_module.normalize_post_button_url("javascript:alert(1)"))


class DeliverPostTest(unittest.IsolatedAsyncioTestCase):
    async def _deliver(self, data: dict, target: int = 111) -> dict:
        bot = SimpleNamespace()
        send = AsyncMock()
        with patch.object(post_module, "send_message_by_type", send):
            await post_module._deliver_post(bot, target, data)
        call = send.await_args
        assert call is not None
        self.assertIs(call.args[0], bot)
        return dict(call.kwargs)

    async def test_sends_text_post_to_given_chat(self):
        kwargs = await self._deliver({"post_html": "<b>hi</b>"})
        self.assertEqual(kwargs["chat_id"], 111)
        self.assertEqual(kwargs["content"].content_type, "text")
        self.assertEqual(kwargs["content"].text, "<b>hi</b>")
        self.assertIsNone(kwargs["reply_markup"])

    async def test_photo_post_with_url_button(self):
        kwargs = await self._deliver(
            {
                "post_html": "post",
                "post_file_id": "photo-id",
                "post_button_url": "https://example.com",
                "post_button_label": "Open",
            },
            target=-100555,
        )
        self.assertEqual(kwargs["chat_id"], -100555)
        self.assertEqual(kwargs["content"].content_type, "photo")
        self.assertEqual(kwargs["content"].file_id, "photo-id")
        markup = cast(types.InlineKeyboardMarkup, kwargs["reply_markup"])
        button = markup.inline_keyboard[0][0]
        self.assertEqual(button.text, "Open")
        self.assertEqual(button.url, "https://example.com")


class PostTextStepTest(unittest.IsolatedAsyncioTestCase):
    async def test_text_goes_to_image_step(self):
        state = _state()
        message = SimpleNamespace(
            html_text="hello <tg-emoji emoji-id='1'>🔥</tg-emoji>",
            photo=None,
            answer=AsyncMock(),
        )
        await post_module.process_post_text_handler(
            cast(types.Message, message), state, _i18n_data(), settings_stub()
        )
        state.update_data.assert_awaited_once_with(
            post_html="hello <tg-emoji emoji-id='1'>🔥</tg-emoji>"
        )
        state.set_state.assert_awaited_once()

    async def test_photo_with_caption_skips_image_step(self):
        state = _state()
        message = SimpleNamespace(
            html_text="caption",
            photo=[SimpleNamespace(file_id="small"), SimpleNamespace(file_id="big")],
            answer=AsyncMock(),
        )
        await post_module.process_post_text_handler(
            cast(types.Message, message), state, _i18n_data(), settings_stub()
        )
        state.update_data.assert_any_await(post_file_id="big")

    async def test_empty_message_asks_for_text(self):
        state = _state()
        message = SimpleNamespace(html_text="  ", photo=None, answer=AsyncMock())
        await post_module.process_post_text_handler(
            cast(types.Message, message), state, _i18n_data(), settings_stub()
        )
        message.answer.assert_awaited_once()
        state.update_data.assert_not_awaited()


class PostButtonStepsTest(unittest.IsolatedAsyncioTestCase):
    async def test_invalid_url_re_asks(self):
        state = _state()
        message = SimpleNamespace(text="not a url", answer=AsyncMock())
        await post_module.process_post_button_url_handler(
            cast(types.Message, message), state, _i18n_data(), settings_stub()
        )
        state.update_data.assert_not_awaited()
        message.answer.assert_awaited_once()

    async def test_valid_url_moves_to_label_step(self):
        state = _state()
        message = SimpleNamespace(text="example.com", answer=AsyncMock())
        await post_module.process_post_button_url_handler(
            cast(types.Message, message), state, _i18n_data(), settings_stub()
        )
        state.update_data.assert_awaited_once_with(post_button_url="https://example.com")
        state.set_state.assert_awaited_once()

    async def test_label_asks_send_target(self):
        state = _state({"post_html": "hi", "post_button_url": "https://example.com"})
        message = SimpleNamespace(text="Open", chat=SimpleNamespace(id=42), answer=AsyncMock())
        await post_module.process_post_button_label_handler(
            cast(types.Message, message), state, _i18n_data(), settings_stub()
        )
        state.update_data.assert_awaited_once_with(post_button_label="Open")
        state.set_state.assert_awaited_once()
        message.answer.assert_awaited_once()


class PostSendTest(unittest.IsolatedAsyncioTestCase):
    def _callback(self, data: str, chat_id: int = 42) -> Any:
        return SimpleNamespace(
            data=data,
            message=SimpleNamespace(
                chat=SimpleNamespace(id=chat_id), answer=AsyncMock(), edit_text=AsyncMock()
            ),
            answer=AsyncMock(),
        )

    async def test_test_send_goes_to_admin_chat(self):
        state = _state({"post_html": "hi"})
        callback = self._callback("admin_post:send_test", chat_id=42)
        with patch.object(post_module, "send_message_by_type", AsyncMock()) as send:
            await post_module.post_send_handler(
                cast(types.CallbackQuery, callback),
                state,
                _i18n_data(),
                settings_stub(ADMIN_POST_CHAT_ID=-100555),
                cast(Bot, SimpleNamespace()),
            )
        self.assertEqual(send.await_args.kwargs["chat_id"], 42)
        state.clear.assert_not_awaited()

    async def test_group_send_goes_to_configured_chat(self):
        state = _state({"post_html": "hi"})
        callback = self._callback("admin_post:send_group", chat_id=42)
        with patch.object(post_module, "send_message_by_type", AsyncMock()) as send:
            await post_module.post_send_handler(
                cast(types.CallbackQuery, callback),
                state,
                _i18n_data(),
                settings_stub(ADMIN_POST_CHAT_ID=-100555),
                cast(Bot, SimpleNamespace()),
            )
        self.assertEqual(send.await_args.kwargs["chat_id"], -100555)
        state.clear.assert_awaited_once()

    async def test_group_send_without_config_alerts(self):
        state = _state({"post_html": "hi"})
        callback = self._callback("admin_post:send_group", chat_id=42)
        with patch.object(post_module, "send_message_by_type", AsyncMock()) as send:
            await post_module.post_send_handler(
                cast(types.CallbackQuery, callback),
                state,
                _i18n_data(),
                settings_stub(ADMIN_POST_CHAT_ID=None),
                cast(Bot, SimpleNamespace()),
            )
        send.assert_not_awaited()
        callback.answer.assert_awaited_once()
        state.clear.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
