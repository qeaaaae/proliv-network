"""Admin giveaway section: composer, participants, and winner draw.

Mirrors the single-shot admin post composer (``post.py``): the admin builds
the announcement step by step - text, an optional photo - then sends a test
copy to their own chat or publishes it to ``ADMIN_POST_CHAT_ID``. Publishing
creates a giveaway row and attaches a "Participate" deep-link button
(``?start=giveaway_<id>``); joining is handled by the user-side giveaway
handler with fixed conditions: channel member + active subscription.
"""

import logging
import re
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta, timezone
from typing import Any

from aiogram import Bot, F, Router, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline.admin_keyboards import (
    get_admin_panel_keyboard,
    get_back_to_admin_panel_keyboard,
    get_giveaway_after_test_keyboard,
    get_giveaway_cancel_confirm_keyboard,
    get_giveaway_confirm_keyboard,
    get_giveaway_draw_confirm_keyboard,
    get_giveaway_menu_keyboard,
    get_giveaway_participants_keyboard,
    get_giveaway_participate_keyboard,
    get_giveaway_step_keyboard,
)
from bot.middlewares.i18n import JsonI18n
from bot.services.giveaway_service import (
    draw_giveaway_winners,
    participant_label,
    refresh_participate_button,
)
from bot.services.subscription_service_impl.core import SubscriptionService
from bot.states.admin_states import AdminStates
from bot.utils.callback_answer import callback_data, callback_message
from bot.utils.mini_app_url import bot_start_deep_link
from config.settings import Settings
from db.dal import giveaway_dal
from db.giveaway_models import GIVEAWAY_STATUS_ACTIVE, GIVEAWAY_STATUS_DRAFT, Giveaway
from db.models import User

logger = logging.getLogger(__name__)

router = Router(name="admin_giveaway_router")

# Telegram photo-caption limit; the HTML copy (tags included) must fit it.
GIVEAWAY_TEXT_LIMIT = 1024
GIVEAWAY_PARTICIPANTS_PAGE_SIZE = 15
GIVEAWAY_START_PARAM_PREFIX = "giveaway_"
# Admin enters the draw time in Moscow time (fixed UTC+3, no DST in Russia).
GIVEAWAY_SCHEDULE_TZ = timezone(timedelta(hours=3))
_GIVEAWAY_SCHEDULE_RE = re.compile(
    r"^\s*(\d{1,2})\.(\d{1,2})(?:\.(\d{2,4}))?\s+(\d{1,2})[:.](\d{2})\s*$"
)

_GIVEAWAY_STATUS_KEYS = {
    GIVEAWAY_STATUS_DRAFT: "admin_giveaway_status_draft",
    GIVEAWAY_STATUS_ACTIVE: "admin_giveaway_status_active",
    "finished": "admin_giveaway_status_finished",
    "cancelled": "admin_giveaway_status_cancelled",
}


def _resolve(i18n_data: dict, settings: Settings) -> tuple[str, JsonI18n | None]:
    return i18n_data.get("current_language", settings.DEFAULT_LANGUAGE), i18n_data.get(
        "i18n_instance"
    )


def _participant_label(user: User) -> str:
    return participant_label(user)


def parse_giveaway_schedule(raw: str, *, now: datetime | None = None) -> datetime | None:
    """Parse "дд.мм[.гг[гг]] чч:мм" in Moscow time into a UTC datetime.

    Returns None for malformed input or a moment in the past.
    """
    match = _GIVEAWAY_SCHEDULE_RE.match(raw or "")
    if not match:
        return None
    day, month = int(match.group(1)), int(match.group(2))
    year_raw = match.group(3)
    hour, minute = int(match.group(4)), int(match.group(5))
    ref = now or datetime.now(UTC)
    ref_local = ref.astimezone(GIVEAWAY_SCHEDULE_TZ)
    if year_raw is None:
        year = ref_local.year
    else:
        year = int(year_raw)
        if year < 100:
            year += 2000
    try:
        local_dt = datetime(year, month, day, hour, minute, tzinfo=GIVEAWAY_SCHEDULE_TZ)
    except ValueError:
        return None
    if local_dt <= ref_local:
        return None
    return local_dt.astimezone(UTC)


def format_giveaway_schedule(when: datetime | None) -> str:
    if when is None:
        return ""
    aware = when if when.tzinfo else when.replace(tzinfo=UTC)
    return aware.astimezone(GIVEAWAY_SCHEDULE_TZ).strftime("%d.%m.%Y %H:%M МСК")


def _giveaway_status_label(_: Callable[..., str], giveaway: Giveaway) -> str:
    key = _GIVEAWAY_STATUS_KEYS.get(str(giveaway.status), "admin_giveaway_status_draft")
    return _(key)


async def _giveaway_menu_text(
    _: Callable[..., str], session: AsyncSession
) -> tuple[str, Giveaway | None, int]:
    giveaway = await giveaway_dal.get_latest_giveaway(session)
    if giveaway is None:
        return _("admin_giveaway_menu_empty"), None, 0
    participants = await giveaway_dal.count_participants(session, int(giveaway.giveaway_id))
    text = _(
        "admin_giveaway_menu_card",
        giveaway_id=int(giveaway.giveaway_id),
        status=_giveaway_status_label(_, giveaway),
        participants=participants,
        winners_count=int(giveaway.winners_count or 3),
        scheduled=(
            _(
                "admin_giveaway_scheduled_at",
                when=format_giveaway_schedule(giveaway.scheduled_draw_at),
            )
            if giveaway.scheduled_draw_at
            else ""
        ),
        display=(
            _("admin_giveaway_display_at", count=int(giveaway.display_participants))
            if giveaway.display_participants is not None
            else ""
        ),
    )
    return text, giveaway, participants


async def _render_giveaway_menu(
    target_message: types.Message,
    session: AsyncSession,
    _: Callable[..., str],
) -> None:
    text, giveaway, _participants = await _giveaway_menu_text(_, session)
    await target_message.edit_text(
        text,
        reply_markup=get_giveaway_menu_keyboard(
            _,
            int(giveaway.giveaway_id) if giveaway is not None else None,
            is_active=bool(giveaway is not None and giveaway.status == GIVEAWAY_STATUS_ACTIVE),
        ),
        parse_mode="HTML",
    )


async def giveaway_menu_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    i18n_data: dict,
    settings: Settings,
    session: AsyncSession,
) -> None:
    """Admin panel "Giveaway" entry: menu with the latest giveaway card."""
    lang, i18n = _resolve(i18n_data, settings)
    if not i18n or not callback.message:
        await callback.answer("Language service error.", show_alert=True)
        return
    _ = lambda key, **kwargs: i18n.gettext(lang, key, **kwargs)

    await state.clear()
    text, giveaway, _participants = await _giveaway_menu_text(_, session)
    markup = get_giveaway_menu_keyboard(
        _,
        int(giveaway.giveaway_id) if giveaway is not None else None,
        is_active=bool(giveaway is not None and giveaway.status == GIVEAWAY_STATUS_ACTIVE),
    )
    try:
        await callback_message(callback).edit_text(text, reply_markup=markup)
    except Exception as e:
        logger.warning("Could not edit message for giveaway menu: %s. Sending new.", e)
        await callback_message(callback).answer(text, reply_markup=markup)
    await callback.answer()


@router.callback_query(F.data == "admin_giveaway:menu")
async def giveaway_menu_back_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    i18n_data: dict,
    settings: Settings,
    session: AsyncSession,
) -> None:
    await state.clear()
    await giveaway_menu_handler(callback, state, i18n_data, settings, session)


async def _ask_image(
    answer: Callable[..., Awaitable[Any]],
    state: FSMContext,
    _: Callable[..., str],
) -> None:
    await answer(
        _("admin_giveaway_enter_image"),
        reply_markup=get_giveaway_step_keyboard(_, skip_callback="admin_giveaway:skip_image"),
    )
    await state.set_state(AdminStates.waiting_for_giveaway_image)


async def _ask_schedule(
    answer: Callable[..., Awaitable[Any]],
    state: FSMContext,
    _: Callable[..., str],
) -> None:
    await answer(
        _("admin_giveaway_enter_schedule"),
        reply_markup=get_giveaway_step_keyboard(_, skip_callback="admin_giveaway:skip_schedule"),
    )
    await state.set_state(AdminStates.waiting_for_giveaway_schedule)


async def _ask_send_target(
    answer: Callable[..., Awaitable[Any]],
    state: FSMContext,
    session: AsyncSession,
    callback_or_message_chat_id: int | None,
    _: Callable[..., str],
) -> None:
    """Final composer step: persist a draft row (the deep link needs an id)."""
    data = await state.get_data()
    raw_scheduled = data.get("giveaway_scheduled_at")
    scheduled_at = datetime.fromisoformat(raw_scheduled) if isinstance(raw_scheduled, str) else None
    giveaway = await giveaway_dal.create_giveaway(
        session,
        text_html=str(data.get("giveaway_html") or ""),
        photo_file_id=data.get("giveaway_file_id"),
        created_by_telegram_id=callback_or_message_chat_id,
        scheduled_draw_at=scheduled_at,
    )
    await state.update_data(giveaway_id=int(giveaway.giveaway_id))
    await answer(
        _("admin_giveaway_ready_prompt"),
        reply_markup=get_giveaway_confirm_keyboard(_),
    )
    await state.set_state(AdminStates.confirming_giveaway)


@router.callback_query(F.data == "admin_giveaway:new")
async def giveaway_new_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    i18n_data: dict,
    settings: Settings,
) -> None:
    """Start the composer: reset any stale flow and ask for the post text."""
    lang, i18n = _resolve(i18n_data, settings)
    if not i18n:
        logger.error("i18n missing in giveaway_new_handler")
        await callback.answer("Language service error.", show_alert=True)
        return
    _ = lambda key, **kwargs: i18n.gettext(lang, key, **kwargs)

    prompt_text = _("admin_giveaway_enter_text")
    prompt_markup = get_giveaway_step_keyboard(_, skip_callback=None)
    if callback.message:
        try:
            await callback_message(callback).edit_text(prompt_text, reply_markup=prompt_markup)
        except Exception as e:
            logger.warning("Could not edit message for giveaway prompt: %s. Sending new.", e)
            await callback_message(callback).answer(prompt_text, reply_markup=prompt_markup)
    await callback.answer()
    await state.clear()
    await state.set_state(AdminStates.waiting_for_giveaway_text)


@router.message(AdminStates.waiting_for_giveaway_text)
async def process_giveaway_text_handler(
    message: types.Message,
    state: FSMContext,
    i18n_data: dict,
    settings: Settings,
    session: AsyncSession,
) -> None:
    lang, i18n = _resolve(i18n_data, settings)
    _ = lambda key, **kwargs: i18n.gettext(lang, key, **kwargs) if i18n else key

    giveaway_html = (message.html_text or "").strip()
    photo_id = message.photo[-1].file_id if message.photo else None
    if not giveaway_html:
        await message.answer(_("admin_giveaway_error_no_text"))
        return
    if len(giveaway_html) > GIVEAWAY_TEXT_LIMIT:
        await message.answer(
            _("admin_giveaway_text_too_long", max_length=GIVEAWAY_TEXT_LIMIT),
            reply_markup=get_giveaway_step_keyboard(_, skip_callback=None),
        )
        return

    await state.update_data(giveaway_html=giveaway_html)
    if photo_id:
        await state.update_data(giveaway_file_id=photo_id)
        await _ask_schedule(message.answer, state, _)
        return
    await _ask_image(message.answer, state, _)


@router.message(AdminStates.waiting_for_giveaway_image)
async def process_giveaway_image_handler(
    message: types.Message,
    state: FSMContext,
    i18n_data: dict,
    settings: Settings,
    session: AsyncSession,
) -> None:
    lang, i18n = _resolve(i18n_data, settings)
    _ = lambda key, **kwargs: i18n.gettext(lang, key, **kwargs) if i18n else key
    if not message.photo:
        await message.answer(
            _("admin_giveaway_error_no_image"),
            reply_markup=get_giveaway_step_keyboard(_, skip_callback="admin_giveaway:skip_image"),
        )
        return
    await state.update_data(giveaway_file_id=message.photo[-1].file_id)
    await _ask_schedule(message.answer, state, _)


@router.callback_query(
    F.data == "admin_giveaway:skip_image", AdminStates.waiting_for_giveaway_image
)
async def skip_giveaway_image_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    i18n_data: dict,
    settings: Settings,
    session: AsyncSession,
) -> None:
    lang, i18n = _resolve(i18n_data, settings)
    _ = lambda key, **kwargs: i18n.gettext(lang, key, **kwargs) if i18n else key
    await state.update_data(giveaway_file_id=None)
    await _ask_schedule(callback_message(callback).answer, state, _)
    await callback.answer()


@router.message(AdminStates.waiting_for_giveaway_schedule)
async def process_giveaway_schedule_handler(
    message: types.Message,
    state: FSMContext,
    i18n_data: dict,
    settings: Settings,
    session: AsyncSession,
) -> None:
    lang, i18n = _resolve(i18n_data, settings)
    _ = lambda key, **kwargs: i18n.gettext(lang, key, **kwargs) if i18n else key
    when = parse_giveaway_schedule(message.text or "")
    if when is None:
        await message.answer(
            _("admin_giveaway_invalid_schedule"),
            reply_markup=get_giveaway_step_keyboard(
                _, skip_callback="admin_giveaway:skip_schedule"
            ),
        )
        return
    await state.update_data(giveaway_scheduled_at=when.isoformat())
    await _ask_send_target(message.answer, state, session, message.chat.id, _)


@router.callback_query(
    F.data == "admin_giveaway:skip_schedule", AdminStates.waiting_for_giveaway_schedule
)
async def skip_giveaway_schedule_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    i18n_data: dict,
    settings: Settings,
    session: AsyncSession,
) -> None:
    lang, i18n = _resolve(i18n_data, settings)
    _ = lambda key, **kwargs: i18n.gettext(lang, key, **kwargs) if i18n else key
    await state.update_data(giveaway_scheduled_at=None)
    await _ask_send_target(
        callback_message(callback).answer, state, session, callback.from_user.id, _
    )
    await callback.answer()


async def _deliver_giveaway(
    bot: Bot,
    target_chat_id: int,
    data: dict,
    participate_url: str | None,
    button_label: str,
) -> types.Message:
    """Send the composed giveaway announcement to the given chat."""
    giveaway_html = str(data.get("giveaway_html") or "").strip()
    file_id = data.get("giveaway_file_id")
    markup = None
    if participate_url:
        markup = get_giveaway_participate_keyboard(participate_url, button_label)
    if file_id:
        return await bot.send_photo(
            chat_id=target_chat_id,
            photo=str(file_id),
            caption=giveaway_html or None,
            parse_mode="HTML",
            reply_markup=markup,
        )
    return await bot.send_message(
        chat_id=target_chat_id,
        text=giveaway_html,
        parse_mode="HTML",
        reply_markup=markup,
    )


@router.callback_query(
    F.data.regexp(r"^admin_giveaway:send_(test|group)$"), AdminStates.confirming_giveaway
)
async def giveaway_send_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    i18n_data: dict,
    settings: Settings,
    session: AsyncSession,
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

    data = await state.get_data()
    giveaway_id = data.get("giveaway_id")
    giveaway = (
        await giveaway_dal.get_giveaway(session, int(giveaway_id))
        if giveaway_id is not None
        else None
    )
    if giveaway is None:
        await callback.answer(_("admin_giveaway_draft_expired"), show_alert=True)
        await state.clear()
        return

    bot_username = None
    try:
        bot_username = (await bot.get_me()).username
    except Exception as e:
        logger.warning("Giveaway send: failed to resolve bot username: %s", e)
    participate_url = bot_start_deep_link(
        bot_username, f"{GIVEAWAY_START_PARAM_PREFIX}{int(giveaway.giveaway_id)}"
    )
    if participate_url is None:
        logger.warning("Giveaway send: bot username unresolved, post goes without button")

    target = (
        int(settings.ADMIN_POST_CHAT_ID)
        if to_group and settings.ADMIN_POST_CHAT_ID
        else callback_message(callback).chat.id
    )
    # Answer early: group delivery can take seconds for photo upload, and an
    # unanswered callback leaves the client-side button spinning forever.
    await callback.answer()
    back_markup = get_back_to_admin_panel_keyboard(lang, i18n)
    try:
        sent = await _deliver_giveaway(
            bot, target, data, participate_url, _("giveaway_participate_button")
        )
    except TelegramBadRequest as error:
        logger.warning("Admin giveaway delivery to %s failed: %s", target, error)
        await callback_message(callback).answer(
            _("admin_giveaway_send_failed", error=str(error)),
            reply_markup=back_markup,
        )
        return

    if to_group:
        await giveaway_dal.publish_giveaway(
            session, giveaway, chat_id=target, message_id=int(sent.message_id)
        )
        try:
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.exception("Giveaway %s publish commit failed: %s", giveaway.giveaway_id, e)
            await callback_message(callback).answer(
                _("admin_giveaway_send_failed", error=str(e)),
                reply_markup=back_markup,
            )
            return
        await callback_message(callback).answer(
            _("admin_giveaway_sent_group"),
            reply_markup=back_markup,
        )
        await state.clear()
    else:
        # Test send keeps the draft alive: the admin can still publish to the
        # group. Only the group publish (or cancel) closes the flow.
        await callback_message(callback).answer(
            _("admin_post_sent_test"),
            reply_markup=get_giveaway_after_test_keyboard(_),
        )


@router.callback_query(F.data.regexp(r"^admin_giveaway:send_(test|group)$"))
async def giveaway_send_stale_handler(callback: types.CallbackQuery) -> None:
    """Stale send buttons (draft cleared/restarted) must not spin forever."""
    await callback.answer(
        "Giveaway draft expired. Open /admin → Giveaway to start over.", show_alert=True
    )


@router.callback_query(F.data == "admin_giveaway:cancel")
async def cancel_giveaway_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    i18n_data: dict,
    settings: Settings,
    session: AsyncSession,
) -> None:
    """Composer cancel: drop the draft row (if created) and return to panel."""
    lang, i18n = _resolve(i18n_data, settings)
    if not i18n or not callback.message:
        await callback.answer("Error cancelling.", show_alert=True)
        return
    _ = lambda key, **kwargs: i18n.gettext(lang, key, **kwargs)

    data = await state.get_data()
    giveaway_id = data.get("giveaway_id")
    if giveaway_id is not None:
        giveaway = await giveaway_dal.get_giveaway(session, int(giveaway_id))
        if giveaway is not None:
            await giveaway_dal.discard_draft(session, giveaway)
            try:
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.exception("Giveaway draft discard failed: %s", e)
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
    await callback.answer(_("admin_giveaway_cancelled"))


@router.callback_query(F.data.regexp(r"^admin_giveaway:list:(\d+):(\d+)$"))
async def giveaway_participants_handler(
    callback: types.CallbackQuery,
    i18n_data: dict,
    settings: Settings,
    session: AsyncSession,
) -> None:
    lang, i18n = _resolve(i18n_data, settings)
    if not i18n or not callback.message:
        await callback.answer("Error.", show_alert=True)
        return
    _ = lambda key, **kwargs: i18n.gettext(lang, key, **kwargs)

    parts = callback_data(callback).split(":")
    giveaway_id = int(parts[2])
    page = int(parts[3])
    giveaway = await giveaway_dal.get_giveaway(session, giveaway_id)
    if giveaway is None:
        await callback.answer(_("admin_giveaway_not_found"), show_alert=True)
        return

    total = await giveaway_dal.count_participants(session, giveaway_id)
    total_pages = max(
        1, (total + GIVEAWAY_PARTICIPANTS_PAGE_SIZE - 1) // GIVEAWAY_PARTICIPANTS_PAGE_SIZE
    )
    page = min(max(page, 0), total_pages - 1)
    rows = await giveaway_dal.list_participants(
        session,
        giveaway_id,
        offset=page * GIVEAWAY_PARTICIPANTS_PAGE_SIZE,
        limit=GIVEAWAY_PARTICIPANTS_PAGE_SIZE,
    )

    lines = [
        _(
            "admin_giveaway_participants_title",
            giveaway_id=giveaway_id,
            total=total,
        )
    ]
    for index, (participant, user) in enumerate(
        rows, start=page * GIVEAWAY_PARTICIPANTS_PAGE_SIZE + 1
    ):
        place = ""
        if participant.place:
            place = _("admin_giveaway_place_mark", place=participant.place)
        joined = ""
        if participant.joined_at:
            joined = participant.joined_at.strftime("%d.%m %H:%M")
        lines.append(
            _(
                "admin_giveaway_participant_row",
                index=index,
                user=_participant_label(user),
                place=place,
                joined=joined,
            )
        )
    if not rows:
        lines.append(_("admin_giveaway_participants_empty"))

    text = "\n".join(lines)
    markup = get_giveaway_participants_keyboard(
        _,
        giveaway_id,
        page,
        total_pages,
        is_active=giveaway.status == GIVEAWAY_STATUS_ACTIVE,
    )
    try:
        await callback_message(callback).edit_text(text, reply_markup=markup, parse_mode="HTML")
    except Exception as e:
        logger.warning("Giveaway participants edit failed: %s. Sending new.", e)
        await callback_message(callback).answer(text, reply_markup=markup, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin_giveaway:page_display")
async def giveaway_page_display_handler(callback: types.CallbackQuery) -> None:
    await callback.answer()


async def _require_active_giveaway(
    callback: types.CallbackQuery,
    session: AsyncSession,
    _: Callable[..., str],
) -> Giveaway | None:
    parts = callback_data(callback).split(":")
    try:
        giveaway_id = int(parts[2])
    except (IndexError, ValueError):
        await callback.answer(_("admin_giveaway_not_found"), show_alert=True)
        return None
    giveaway = await giveaway_dal.get_giveaway(session, giveaway_id)
    if giveaway is None:
        await callback.answer(_("admin_giveaway_not_found"), show_alert=True)
        return None
    if giveaway.status != GIVEAWAY_STATUS_ACTIVE:
        await callback.answer(_("admin_giveaway_not_active"), show_alert=True)
        return None
    return giveaway


@router.callback_query(F.data.regexp(r"^admin_giveaway:draw:\d+$"))
async def giveaway_draw_prompt_handler(
    callback: types.CallbackQuery,
    i18n_data: dict,
    settings: Settings,
    session: AsyncSession,
) -> None:
    lang, i18n = _resolve(i18n_data, settings)
    if not i18n or not callback.message:
        await callback.answer("Error.", show_alert=True)
        return
    _ = lambda key, **kwargs: i18n.gettext(lang, key, **kwargs)
    giveaway = await _require_active_giveaway(callback, session, _)
    if giveaway is None:
        return
    participants = await giveaway_dal.count_participants(session, int(giveaway.giveaway_id))
    text = _(
        "admin_giveaway_draw_confirm_text",
        giveaway_id=int(giveaway.giveaway_id),
        participants=participants,
        winners_count=int(giveaway.winners_count or 3),
    )
    try:
        await callback_message(callback).edit_text(
            text,
            reply_markup=get_giveaway_draw_confirm_keyboard(_, int(giveaway.giveaway_id)),
        )
    except Exception:
        await callback_message(callback).answer(
            text,
            reply_markup=get_giveaway_draw_confirm_keyboard(_, int(giveaway.giveaway_id)),
        )
    await callback.answer()


@router.callback_query(F.data.regexp(r"^admin_giveaway:draw_confirm:\d+$"))
async def giveaway_draw_handler(
    callback: types.CallbackQuery,
    i18n_data: dict,
    settings: Settings,
    session: AsyncSession,
    subscription_service: SubscriptionService,
    bot: Bot,
) -> None:
    lang, i18n = _resolve(i18n_data, settings)
    if not i18n or not callback.message:
        await callback.answer("Error.", show_alert=True)
        return
    _ = lambda key, **kwargs: i18n.gettext(lang, key, **kwargs)
    giveaway = await _require_active_giveaway(callback, session, _)
    if giveaway is None:
        return

    await callback.answer()
    winners = await draw_giveaway_winners(session, giveaway)
    await giveaway_dal.finish_giveaway(session, giveaway)
    try:
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.exception("Giveaway %s draw commit failed: %s", giveaway.giveaway_id, e)
        await callback_message(callback).answer(
            _("admin_giveaway_draw_failed", error=str(e)),
            reply_markup=get_back_to_admin_panel_keyboard(lang, i18n),
        )
        return

    winners_lines = [
        _("admin_giveaway_winner_row", place=place, user=_participant_label(user))
        for place, user in winners
    ]
    winners_block = "\n".join(winners_lines) if winners_lines else _("admin_giveaway_no_winners")
    result_text = _(
        "admin_giveaway_results_text",
        giveaway_id=int(giveaway.giveaway_id),
        winners=winners_block,
    )
    back_markup = get_back_to_admin_panel_keyboard(lang, i18n)
    try:
        await callback_message(callback).edit_text(
            result_text, reply_markup=back_markup, parse_mode="HTML"
        )
    except Exception:
        await callback_message(callback).answer(
            result_text, reply_markup=back_markup, parse_mode="HTML"
        )

    # Announce the results in the group as a reply to the giveaway post.
    if giveaway.chat_id:
        try:
            await bot.send_message(
                chat_id=int(giveaway.chat_id),
                text=_("admin_giveaway_group_results", winners=winners_block),
                parse_mode="HTML",
                reply_to_message_id=(int(giveaway.message_id) if giveaway.message_id else None),
                allow_sending_without_reply=True,
            )
        except Exception as e:
            logger.warning("Giveaway %s group announce failed: %s", giveaway.giveaway_id, e)


@router.callback_query(F.data.regexp(r"^admin_giveaway:cancel_gw:\d+$"))
async def giveaway_cancel_prompt_handler(
    callback: types.CallbackQuery,
    i18n_data: dict,
    settings: Settings,
    session: AsyncSession,
) -> None:
    lang, i18n = _resolve(i18n_data, settings)
    if not i18n or not callback.message:
        await callback.answer("Error.", show_alert=True)
        return
    _ = lambda key, **kwargs: i18n.gettext(lang, key, **kwargs)
    giveaway = await _require_active_giveaway(callback, session, _)
    if giveaway is None:
        return
    text = _("admin_giveaway_cancel_confirm_text", giveaway_id=int(giveaway.giveaway_id))
    try:
        await callback_message(callback).edit_text(
            text,
            reply_markup=get_giveaway_cancel_confirm_keyboard(_, int(giveaway.giveaway_id)),
        )
    except Exception:
        await callback_message(callback).answer(
            text,
            reply_markup=get_giveaway_cancel_confirm_keyboard(_, int(giveaway.giveaway_id)),
        )
    await callback.answer()


@router.callback_query(F.data.regexp(r"^admin_giveaway:cancel_confirm:\d+$"))
async def giveaway_cancel_gw_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    i18n_data: dict,
    settings: Settings,
    session: AsyncSession,
) -> None:
    lang, i18n = _resolve(i18n_data, settings)
    if not i18n or not callback.message:
        await callback.answer("Error.", show_alert=True)
        return
    _ = lambda key, **kwargs: i18n.gettext(lang, key, **kwargs)
    giveaway = await _require_active_giveaway(callback, session, _)
    if giveaway is None:
        return
    await giveaway_dal.cancel_giveaway(session, giveaway)
    try:
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.exception("Giveaway %s cancel commit failed: %s", giveaway.giveaway_id, e)
        await callback.answer(_("error_occurred_try_again"), show_alert=True)
        return
    await callback.answer(_("admin_giveaway_cancelled_gw"))
    await giveaway_menu_handler(callback, state, i18n_data, settings, session)


@router.callback_query(F.data.regexp(r"^admin_giveaway:schedule:\d+$"))
async def giveaway_schedule_prompt_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    i18n_data: dict,
    settings: Settings,
    session: AsyncSession,
) -> None:
    """Menu "schedule" button on a published giveaway: ask for the draw time."""
    lang, i18n = _resolve(i18n_data, settings)
    if not i18n or not callback.message:
        await callback.answer("Error.", show_alert=True)
        return
    _ = lambda key, **kwargs: i18n.gettext(lang, key, **kwargs)
    giveaway = await _require_active_giveaway(callback, session, _)
    if giveaway is None:
        return
    await state.update_data(reschedule_giveaway_id=int(giveaway.giveaway_id))
    try:
        await callback_message(callback).edit_text(
            _("admin_giveaway_enter_schedule"),
            reply_markup=get_giveaway_step_keyboard(
                _, skip_callback="admin_giveaway:clear_schedule"
            ),
        )
    except Exception:
        await callback_message(callback).answer(
            _("admin_giveaway_enter_schedule"),
            reply_markup=get_giveaway_step_keyboard(
                _, skip_callback="admin_giveaway:clear_schedule"
            ),
        )
    await state.set_state(AdminStates.waiting_for_giveaway_reschedule)
    await callback.answer()


@router.callback_query(
    F.data == "admin_giveaway:clear_schedule",
    AdminStates.waiting_for_giveaway_reschedule,
)
async def giveaway_clear_schedule_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    i18n_data: dict,
    settings: Settings,
    session: AsyncSession,
) -> None:
    lang, i18n = _resolve(i18n_data, settings)
    if not i18n or not callback.message:
        await callback.answer("Error.", show_alert=True)
        return
    _ = lambda key, **kwargs: i18n.gettext(lang, key, **kwargs)
    data = await state.get_data()
    giveaway_id = data.get("reschedule_giveaway_id")
    giveaway = (
        await giveaway_dal.get_giveaway(session, int(giveaway_id))
        if giveaway_id is not None
        else None
    )
    if giveaway is not None and giveaway.status == GIVEAWAY_STATUS_ACTIVE:
        await giveaway_dal.schedule_draw(session, giveaway, None)
        try:
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.exception("Giveaway %s schedule clear failed: %s", giveaway.giveaway_id, e)
            await callback.answer(_("error_occurred_try_again"), show_alert=True)
            return
        await callback.answer(_("admin_giveaway_schedule_cleared"))
    else:
        await callback.answer(_("admin_giveaway_not_active"), show_alert=True)
    await state.clear()
    await giveaway_menu_handler(callback, state, i18n_data, settings, session)


@router.message(AdminStates.waiting_for_giveaway_reschedule)
async def process_giveaway_reschedule_handler(
    message: types.Message,
    state: FSMContext,
    i18n_data: dict,
    settings: Settings,
    session: AsyncSession,
) -> None:
    lang, i18n = _resolve(i18n_data, settings)
    _ = lambda key, **kwargs: i18n.gettext(lang, key, **kwargs) if i18n else key
    when = parse_giveaway_schedule(message.text or "")
    if when is None:
        await message.answer(
            _("admin_giveaway_invalid_schedule"),
            reply_markup=get_giveaway_step_keyboard(
                _, skip_callback="admin_giveaway:clear_schedule"
            ),
        )
        return
    data = await state.get_data()
    giveaway_id = data.get("reschedule_giveaway_id")
    giveaway = (
        await giveaway_dal.get_giveaway(session, int(giveaway_id))
        if giveaway_id is not None
        else None
    )
    if giveaway is None or giveaway.status != GIVEAWAY_STATUS_ACTIVE:
        await message.answer(_("admin_giveaway_not_active"))
        await state.clear()
        return
    await giveaway_dal.schedule_draw(session, giveaway, when)
    try:
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.exception("Giveaway %s schedule commit failed: %s", giveaway.giveaway_id, e)
        await message.answer(_("admin_giveaway_send_failed", error=str(e)))
        await state.clear()
        return
    await message.answer(_("admin_giveaway_schedule_set", when=format_giveaway_schedule(when)))
    await state.clear()
    text, active_giveaway, _p = await _giveaway_menu_text(_, session)
    await message.answer(
        text,
        reply_markup=get_giveaway_menu_keyboard(
            _,
            int(active_giveaway.giveaway_id) if active_giveaway is not None else None,
            is_active=bool(
                active_giveaway is not None and active_giveaway.status == GIVEAWAY_STATUS_ACTIVE
            ),
        ),
        parse_mode="HTML",
    )


@router.callback_query(F.data.regexp(r"^admin_giveaway:setcount:\d+$"))
async def giveaway_setcount_prompt_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    i18n_data: dict,
    settings: Settings,
    session: AsyncSession,
) -> None:
    """Menu "button counter" button: ask for the number shown on the post."""
    lang, i18n = _resolve(i18n_data, settings)
    if not i18n or not callback.message:
        await callback.answer("Error.", show_alert=True)
        return
    _ = lambda key, **kwargs: i18n.gettext(lang, key, **kwargs)
    giveaway = await _require_active_giveaway(callback, session, _)
    if giveaway is None:
        return
    await state.update_data(setcount_giveaway_id=int(giveaway.giveaway_id))
    prompt = _("admin_giveaway_enter_counter")
    keyboard = get_giveaway_step_keyboard(_, skip_callback="admin_giveaway:clear_count")
    try:
        await callback_message(callback).edit_text(prompt, reply_markup=keyboard)
    except Exception:
        await callback_message(callback).answer(prompt, reply_markup=keyboard)
    await state.set_state(AdminStates.waiting_for_giveaway_counter)
    await callback.answer()


@router.callback_query(
    F.data == "admin_giveaway:clear_count",
    AdminStates.waiting_for_giveaway_counter,
)
async def giveaway_clear_count_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    i18n_data: dict,
    settings: Settings,
    session: AsyncSession,
    bot: Bot,
) -> None:
    lang, i18n = _resolve(i18n_data, settings)
    if not i18n or not callback.message:
        await callback.answer("Error.", show_alert=True)
        return
    _ = lambda key, **kwargs: i18n.gettext(lang, key, **kwargs)
    data = await state.get_data()
    giveaway_id = data.get("setcount_giveaway_id")
    giveaway = (
        await giveaway_dal.get_giveaway(session, int(giveaway_id))
        if giveaway_id is not None
        else None
    )
    if giveaway is None or giveaway.status != GIVEAWAY_STATUS_ACTIVE:
        await callback.answer(_("admin_giveaway_not_active"), show_alert=True)
        await state.clear()
        return
    await giveaway_dal.set_display_count(session, giveaway, None)
    try:
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.exception("Giveaway %s display count clear failed: %s", giveaway.giveaway_id, e)
        await callback.answer(_("error_occurred_try_again"), show_alert=True)
        return
    await refresh_participate_button(bot, giveaway, _("giveaway_participate_button"), None)
    await callback.answer(_("admin_giveaway_counter_cleared"))
    await state.clear()
    await giveaway_menu_handler(callback, state, i18n_data, settings, session)


@router.message(AdminStates.waiting_for_giveaway_counter)
async def process_giveaway_counter_handler(
    message: types.Message,
    state: FSMContext,
    i18n_data: dict,
    settings: Settings,
    session: AsyncSession,
    bot: Bot,
) -> None:
    lang, i18n = _resolve(i18n_data, settings)
    _ = lambda key, **kwargs: i18n.gettext(lang, key, **kwargs) if i18n else key
    raw = (message.text or "").strip()
    try:
        value = int(raw)
    except ValueError:
        value = -1
    if value < 0:
        await message.answer(
            _("admin_giveaway_invalid_counter"),
            reply_markup=get_giveaway_step_keyboard(_, skip_callback="admin_giveaway:clear_count"),
        )
        return
    data = await state.get_data()
    giveaway_id = data.get("setcount_giveaway_id")
    giveaway = (
        await giveaway_dal.get_giveaway(session, int(giveaway_id))
        if giveaway_id is not None
        else None
    )
    if giveaway is None or giveaway.status != GIVEAWAY_STATUS_ACTIVE:
        await message.answer(_("admin_giveaway_not_active"))
        await state.clear()
        return
    await giveaway_dal.set_display_count(session, giveaway, value)
    try:
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.exception("Giveaway %s display count commit failed: %s", giveaway.giveaway_id, e)
        await message.answer(_("admin_giveaway_send_failed", error=str(e)))
        await state.clear()
        return
    await refresh_participate_button(bot, giveaway, _("giveaway_participate_button"), value)
    await message.answer(_("admin_giveaway_counter_set", count=value))
    await state.clear()
    text, active_giveaway, _p = await _giveaway_menu_text(_, session)
    await message.answer(
        text,
        reply_markup=get_giveaway_menu_keyboard(
            _,
            int(active_giveaway.giveaway_id) if active_giveaway is not None else None,
            is_active=bool(
                active_giveaway is not None and active_giveaway.status == GIVEAWAY_STATUS_ACTIVE
            ),
        ),
        parse_mode="HTML",
    )
