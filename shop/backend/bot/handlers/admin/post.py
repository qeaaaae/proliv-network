"""Single-shot admin post composer.

Unlike the broadcast flow (mass delivery to users), a post is one message
the admin builds step by step: text, an optional photo, and an optional
URL button (link + label). The final step offers two sends: a test copy
to the admin's own chat and a publish to ``ADMIN_POST_CHAT_ID``.
``html_text`` keeps formatting and custom emoji intact and stores cleanly
in FSM state.
"""

import logging
import re
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import Bot, F, Router, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext

from bot.keyboards.inline.admin_keyboards import (
    get_admin_panel_keyboard,
    get_back_to_admin_panel_keyboard,
    get_post_after_test_keyboard,
    get_post_confirm_keyboard,
    get_post_step_keyboard,
)
from bot.middlewares.i18n import JsonI18n
from bot.states.admin_states import AdminStates
from bot.utils import MessageContent, send_message_by_type
from bot.utils.callback_answer import callback_data, callback_message
from config.settings import Settings

logger = logging.getLogger(__name__)

router = Router(name="admin_post_router")

# Telegram photo-caption limit; the HTML copy (tags included) must fit it.
POST_TEXT_LIMIT = 1024
POST_BUTTON_LABEL_LIMIT = 64

_URL_SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*://")
_BARE_DOMAIN_RE = re.compile(r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/\S*)?$")


def normalize_post_button_url(raw: str) -> str | None:
    """Accept http(s)/tg URLs and bare domains (https:// is prepended)."""
    candidate = raw.strip()
    if not candidate:
        return None
    if not _URL_SCHEME_RE.match(candidate):
        if not _BARE_DOMAIN_RE.match(candidate):
            return None
        candidate = f"https://{candidate}"
    scheme = candidate.split(":", 1)[0].lower()
    if scheme not in {"http", "https", "tg"}:
        return None
    return candidate


def _resolve(i18n_data: dict, settings: Settings) -> tuple[str, JsonI18n | None]:
    return i18n_data.get("current_language", settings.DEFAULT_LANGUAGE), i18n_data.get(
        "i18n_instance"
    )


async def _ask_image(
    answer: Callable[..., Awaitable[Any]],
    state: FSMContext,
    _: Callable[..., str],
) -> None:
    await answer(
        _("admin_post_enter_image"),
        reply_markup=get_post_step_keyboard(_, skip_callback="admin_post:skip_image"),
    )
    await state.set_state(AdminStates.waiting_for_post_image)


async def _ask_button_url(
    answer: Callable[..., Awaitable[Any]],
    state: FSMContext,
    _: Callable[..., str],
) -> None:
    await answer(
        _("admin_post_enter_url"),
        reply_markup=get_post_step_keyboard(_, skip_callback="admin_post:skip_button"),
    )
    await state.set_state(AdminStates.waiting_for_post_button_url)


async def _deliver_post(
    bot: Bot,
    target_chat_id: int,
    data: dict,
) -> None:
    """Send the composed post to the given chat."""
    post_html = str(data.get("post_html") or "").strip()
    file_id = data.get("post_file_id")
    url = data.get("post_button_url")
    label = data.get("post_button_label")
    markup = None
    if url and label:
        markup = types.InlineKeyboardMarkup(
            inline_keyboard=[[types.InlineKeyboardButton(text=str(label), url=str(url))]]
        )
    content = MessageContent(
        content_type="photo" if file_id else "text",
        file_id=file_id,
        text=post_html,
    )
    await send_message_by_type(
        bot,
        chat_id=target_chat_id,
        content=content,
        parse_mode="HTML",
        reply_markup=markup,
    )


async def _ask_send_target(
    answer: Callable[..., Awaitable[Any]],
    state: FSMContext,
    _: Callable[..., str],
) -> None:
    """Final composer step: admin picks the test send or the group publish."""
    await answer(
        _("admin_post_ready_prompt"),
        reply_markup=get_post_confirm_keyboard(_),
    )
    await state.set_state(AdminStates.confirming_post)


async def post_prompt_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    i18n_data: dict,
    settings: Settings,
) -> None:
    """Admin panel "Post" entry: resets any stale flow and asks for text."""
    lang, i18n = _resolve(i18n_data, settings)
    if not i18n:
        logger.error("i18n missing in post_prompt_handler")
        await callback.answer("Language service error.", show_alert=True)
        return
    _ = lambda key, **kwargs: i18n.gettext(lang, key, **kwargs)

    prompt_text = _("admin_post_enter_text")
    prompt_markup = get_post_step_keyboard(_, skip_callback=None)
    if callback.message:
        try:
            await callback_message(callback).edit_text(prompt_text, reply_markup=prompt_markup)
        except Exception as e:
            logger.warning("Could not edit message for post prompt: %s. Sending new.", e)
            await callback_message(callback).answer(prompt_text, reply_markup=prompt_markup)
    await callback.answer()
    await state.clear()
    await state.set_state(AdminStates.waiting_for_post_text)


@router.message(AdminStates.waiting_for_post_text)
async def process_post_text_handler(
    message: types.Message,
    state: FSMContext,
    i18n_data: dict,
    settings: Settings,
) -> None:
    lang, i18n = _resolve(i18n_data, settings)
    _ = lambda key, **kwargs: i18n.gettext(lang, key, **kwargs) if i18n else key

    # html_text covers the caption too: a photo with a caption doubles as
    # text + image, so the composer skips the image step.
    post_html = (message.html_text or "").strip()
    photo_id = message.photo[-1].file_id if message.photo else None
    if not post_html:
        await message.answer(_("admin_post_error_no_text"))
        return
    if len(post_html) > POST_TEXT_LIMIT:
        await message.answer(
            _("admin_post_text_too_long", max_length=POST_TEXT_LIMIT),
            reply_markup=get_post_step_keyboard(_, skip_callback=None),
        )
        return

    await state.update_data(post_html=post_html)
    if photo_id:
        await state.update_data(post_file_id=photo_id)
        await _ask_button_url(message.answer, state, _)
        return
    await _ask_image(message.answer, state, _)


@router.message(AdminStates.waiting_for_post_image)
async def process_post_image_handler(
    message: types.Message,
    state: FSMContext,
    i18n_data: dict,
    settings: Settings,
) -> None:
    lang, i18n = _resolve(i18n_data, settings)
    _ = lambda key, **kwargs: i18n.gettext(lang, key, **kwargs) if i18n else key
    if not message.photo:
        await message.answer(
            _("admin_post_error_no_image"),
            reply_markup=get_post_step_keyboard(_, skip_callback="admin_post:skip_image"),
        )
        return
    await state.update_data(post_file_id=message.photo[-1].file_id)
    await _ask_button_url(message.answer, state, _)


@router.callback_query(F.data == "admin_post:skip_image", AdminStates.waiting_for_post_image)
async def skip_post_image_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    i18n_data: dict,
    settings: Settings,
) -> None:
    lang, i18n = _resolve(i18n_data, settings)
    _ = lambda key, **kwargs: i18n.gettext(lang, key, **kwargs) if i18n else key
    await state.update_data(post_file_id=None)
    await _ask_button_url(callback_message(callback).answer, state, _)
    await callback.answer()


@router.message(AdminStates.waiting_for_post_button_url)
async def process_post_button_url_handler(
    message: types.Message,
    state: FSMContext,
    i18n_data: dict,
    settings: Settings,
) -> None:
    lang, i18n = _resolve(i18n_data, settings)
    _ = lambda key, **kwargs: i18n.gettext(lang, key, **kwargs) if i18n else key
    url = normalize_post_button_url(message.text or "")
    if not url:
        await message.answer(
            _("admin_post_invalid_url"),
            reply_markup=get_post_step_keyboard(_, skip_callback="admin_post:skip_button"),
        )
        return
    await state.update_data(post_button_url=url)
    await message.answer(
        _("admin_post_enter_button_label", max_length=POST_BUTTON_LABEL_LIMIT),
        reply_markup=get_post_step_keyboard(_, skip_callback=None),
    )
    await state.set_state(AdminStates.waiting_for_post_button_label)


@router.callback_query(F.data == "admin_post:skip_button", AdminStates.waiting_for_post_button_url)
async def skip_post_button_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    i18n_data: dict,
    settings: Settings,
) -> None:
    lang, i18n = _resolve(i18n_data, settings)
    if not i18n or not callback.message:
        await callback.answer("Error.", show_alert=True)
        return
    _ = lambda key, **kwargs: i18n.gettext(lang, key, **kwargs)
    await state.update_data(post_button_url=None, post_button_label=None)
    await _ask_send_target(callback_message(callback).answer, state, _)
    await callback.answer()


@router.message(AdminStates.waiting_for_post_button_label)
async def process_post_button_label_handler(
    message: types.Message,
    state: FSMContext,
    i18n_data: dict,
    settings: Settings,
) -> None:
    lang, i18n = _resolve(i18n_data, settings)
    _ = lambda key, **kwargs: i18n.gettext(lang, key, **kwargs) if i18n else key
    label = (message.text or "").strip()
    if not label:
        await message.answer(_("admin_post_error_no_label"))
        return
    if len(label) > POST_BUTTON_LABEL_LIMIT:
        await message.answer(
            _("admin_post_label_too_long", max_length=POST_BUTTON_LABEL_LIMIT),
            reply_markup=get_post_step_keyboard(_, skip_callback=None),
        )
        return
    await state.update_data(post_button_label=label)
    if not i18n:
        await message.answer("Language service error.")
        await state.clear()
        return
    await _ask_send_target(message.answer, state, _)


@router.callback_query(
    F.data.regexp(r"^admin_post:send_(test|group)$"), AdminStates.confirming_post
)
async def post_send_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    i18n_data: dict,
    settings: Settings,
    bot: Bot,
) -> None:
    lang, i18n = _resolve(i18n_data, settings)
    if not i18n or not callback.message:
        await callback.answer("Error.", show_alert=True)
        return
    _ = lambda key, **kwargs: i18n.gettext(lang, key, **kwargs)

    to_group = callback_data(callback).endswith("group")
    if to_group and not settings.ADMIN_POST_CHAT_ID:
        await callback.answer(_("admin_post_group_not_configured"), show_alert=True)
        return
    target = (
        int(settings.ADMIN_POST_CHAT_ID)
        if to_group and settings.ADMIN_POST_CHAT_ID
        else callback_message(callback).chat.id
    )
    data = await state.get_data()
    # Answer early: group delivery can take seconds for photo upload, and an
    # unanswered callback leaves the client-side button spinning forever.
    await callback.answer()
    back_markup = get_back_to_admin_panel_keyboard(lang, i18n)
    try:
        await _deliver_post(bot, target, data)
    except TelegramBadRequest as error:
        logger.warning("Admin post delivery to %s failed: %s", target, error)
        await callback_message(callback).answer(
            _("admin_post_send_failed", error=str(error)),
            reply_markup=back_markup,
        )
    else:
        # Test send keeps the draft alive: the admin can still publish to the
        # group. Only the group publish (or cancel) closes the flow.
        await callback_message(callback).answer(
            _("admin_post_sent_group" if to_group else "admin_post_sent_test"),
            reply_markup=(back_markup if to_group else get_post_after_test_keyboard(_)),
        )
    if to_group:
        await state.clear()


@router.callback_query(F.data.regexp(r"^admin_post:send_(test|group)$"))
async def post_send_stale_handler(callback: types.CallbackQuery) -> None:
    """Stale send buttons (draft cleared/restarted) must not spin forever."""
    await callback.answer("Post draft expired. Open /admin → Post to start over.", show_alert=True)


@router.callback_query(F.data == "admin_post:cancel")
async def cancel_post_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    i18n_data: dict,
    settings: Settings,
) -> None:
    lang, i18n = _resolve(i18n_data, settings)
    if not i18n or not callback.message:
        await callback.answer("Error cancelling.", show_alert=True)
        return
    _ = lambda key, **kwargs: i18n.gettext(lang, key, **kwargs)
    await state.clear()
    try:
        await callback_message(callback).edit_text(
            _(key="admin_panel_title"),
            reply_markup=get_admin_panel_keyboard(i18n, lang, settings),
        )
    except Exception:
        await callback_message(callback).answer(
            _(key="admin_panel_title"),
            reply_markup=get_admin_panel_keyboard(i18n, lang, settings),
        )
    await callback.answer(_("admin_post_cancelled"))
