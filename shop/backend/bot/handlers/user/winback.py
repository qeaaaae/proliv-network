"""User-side win-back survey flow.

The survey prompt is sent by ``WinbackSurveyWorker`` ~1 day after the user's
latest subscription expired. Reason callbacks:

- ``winback:r:expensive:<sub>`` - mint a personal -10% promo code and show it;
- ``winback:r:missing_location:<sub>`` - ask for the wanted location as text;
- ``winback:r:unstable:<sub>`` - follow-up mini survey (connection type ->
  time of day -> optional note).

Every completed answer is recorded in ``message_logs`` and forwarded to all
admin DMs. ``winback_survey:answered`` on the lapsed subscription row makes
the survey single-answer across restarts and repeated clicks.
"""

import logging
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from aiogram import Bot, F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from bot.middlewares.i18n import JsonI18n
from bot.services.winback_survey import (
    REASON_LABEL_KEYS,
    find_winback_promo,
    issue_winback_discount,
    mark_survey_answered,
    notify_winback_admins,
    promo_still_redeemable,
    record_winback_response,
    survey_already_answered,
)
from bot.states.user_states import WinbackSurveyStates
from bot.utils.callback_answer import (
    callback_message_or_none,
    message_bot,
    message_from_user,
    safe_answer_callback,
)
from bot.utils.mini_app_url import subscription_mini_app_checkout_code_url
from config.settings import Settings
from db.dal import user_dal
from db.models import Subscription, User

logger = logging.getLogger(__name__)

router = Router(name="user_winback_router")

_CONN_KEYS = {"lte": "winback_conn_lte", "regular": "winback_conn_regular"}
_TIME_KEYS = {
    "morning": "winback_time_morning",
    "day": "winback_time_day",
    "evening": "winback_time_evening",
    "night": "winback_time_night",
}
MAX_WINBACK_TEXT_LENGTH = 400


def _resolve(i18n_data: dict, settings: Settings) -> tuple[str, Callable[..., str]]:
    current_lang = i18n_data.get("current_language", settings.DEFAULT_LANGUAGE)
    i18n: JsonI18n | None = i18n_data.get("i18n_instance")
    if i18n is None:
        return current_lang, lambda key, **kwargs: key
    return current_lang, lambda key, **kwargs: i18n.gettext(current_lang, key, **kwargs)


async def _edit_prompt(
    callback: types.CallbackQuery, text: str, markup: Any = None
) -> None:
    message = callback_message_or_none(callback)
    if message is None:
        return
    try:
        await message.edit_text(text, reply_markup=markup)
    except Exception:
        logger.warning("Failed to edit win-back survey message", exc_info=True)


async def _finish_survey(
    *,
    session: AsyncSession,
    subscription_id: int,
    db_user: User,
    audit_content: str,
    bot: Bot | None,
    settings: Settings,
    i18n_data: dict,
    admin_lines: list[str],
) -> None:
    await mark_survey_answered(session, subscription_id, sent_at=datetime.now(UTC))
    await record_winback_response(session, db_user, content=audit_content)
    await session.commit()
    i18n: JsonI18n | None = i18n_data.get("i18n_instance")
    if i18n is None:
        return
    await notify_winback_admins(
        bot=bot,
        session=session,
        settings=settings,
        i18n=i18n,
        user=db_user,
        telegram_id=int(getattr(db_user, "telegram_id", 0) or 0),
        detail_lines=admin_lines,
    )


async def _reason_detail(
    reason: str, i18n: JsonI18n | None, lang: str
) -> str:
    label_key = REASON_LABEL_KEYS.get(reason)
    if i18n is None or label_key is None:
        return reason
    return str(i18n.gettext(lang, label_key))


@router.callback_query(
    F.data.regexp(r"^winback:r:(expensive|missing_location|unstable):(\d+)$")
)
async def winback_reason_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    settings: Settings,
    i18n_data: dict,
    session: AsyncSession,
) -> None:
    current_lang, _ = _resolve(i18n_data, settings)
    parts = (callback.data or "").split(":")
    if len(parts) != 4:
        await safe_answer_callback(
            callback, _("error_occurred_try_again"), show_alert=True
        )
        return
    reason, raw_sub_id = parts[2], parts[3]
    try:
        subscription_id = int(raw_sub_id)
    except ValueError:
        await safe_answer_callback(
            callback, _("error_occurred_try_again"), show_alert=True
        )
        return

    db_user = await user_dal.get_user_by_telegram_id(session, callback.from_user.id)
    if db_user is None:
        await safe_answer_callback(
            callback, _("error_occurred_try_again"), show_alert=True
        )
        return
    sub = await session.get(Subscription, subscription_id)
    if sub is None or int(sub.user_id) != int(db_user.user_id):
        await safe_answer_callback(
            callback, _("error_occurred_try_again"), show_alert=True
        )
        return
    if await survey_already_answered(session, subscription_id):
        await safe_answer_callback(callback, _("winback_already_answered"))
        return

    i18n: JsonI18n | None = i18n_data.get("i18n_instance")

    if reason == "expensive":
        promo = await find_winback_promo(session, int(db_user.user_id))
        reshow = promo is not None
        if promo is not None and not promo_still_redeemable(promo):
            reason_text = await _reason_detail(reason, i18n, current_lang)
            await _finish_survey(
                session=session,
                subscription_id=subscription_id,
                db_user=db_user,
                audit_content="reason=expensive promo=already_received",
                bot=callback.bot,
                settings=settings,
                i18n_data=i18n_data,
                admin_lines=[reason_text, "promo=already_received"],
            )
            await _edit_prompt(callback, _("winback_discount_already_received"))
            await safe_answer_callback(callback)
            return
        if promo is None:
            try:
                promo = await issue_winback_discount(session, db_user)
            except Exception:
                await session.rollback()
                logger.exception(
                    "Win-back discount issue failed for user %s", db_user.user_id
                )
                await safe_answer_callback(
                    callback, _("error_occurred_try_again"), show_alert=True
                )
                return
        valid_until = getattr(promo, "valid_until", None)
        valid_until_text = (
            valid_until.strftime("%d.%m.%Y") if isinstance(valid_until, datetime) else ""
        )
        reason_text = await _reason_detail(reason, i18n, current_lang)
        suffix = ", re-shown" if reshow else ""
        await _finish_survey(
            session=session,
            subscription_id=subscription_id,
            db_user=db_user,
            audit_content=(
                f"reason=expensive promo={promo.code} discount=10%"
                f"{' reshow' if reshow else ''}"
            ),
            bot=callback.bot,
            settings=settings,
            i18n_data=i18n_data,
            admin_lines=[
                reason_text,
                f"promo={promo.code} (-10%, until {valid_until_text}{suffix})",
            ],
        )
        builder = InlineKeyboardBuilder()
        checkout_url = subscription_mini_app_checkout_code_url(settings, str(promo.code))
        if checkout_url:
            builder.button(
                text=_("winback_discount_use_button"),
                web_app=types.WebAppInfo(url=checkout_url),
            )
            builder.adjust(1)
        await _edit_prompt(
            callback,
            _(
                "winback_discount_granted",
                code=promo.code,
                discount="10",
                date=valid_until_text,
            ),
            builder.as_markup() if checkout_url else None,
        )
        await safe_answer_callback(callback)
        return

    if reason == "missing_location":
        await state.update_data(winback_sub=subscription_id)
        await state.set_state(WinbackSurveyStates.waiting_for_location)
        await _edit_prompt(callback, _("winback_ask_location"))
        await safe_answer_callback(callback)
        return

    if reason == "unstable":
        await state.update_data(winback_sub=subscription_id)
        builder = InlineKeyboardBuilder()
        for conn_key, label_key in _CONN_KEYS.items():
            builder.button(text=_(label_key), callback_data=f"winback:c:{conn_key}")
        builder.adjust(2)
        await _edit_prompt(
            callback, _("winback_unstable_ask_conn"), builder.as_markup()
        )
        await safe_answer_callback(callback)
        return

    await safe_answer_callback(
        callback, _("error_occurred_try_again"), show_alert=True
    )


@router.callback_query(F.data.regexp(r"^winback:c:(lte|regular)$"))
async def winback_conn_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    settings: Settings,
    i18n_data: dict,
) -> None:
    _current_lang, _ = _resolve(i18n_data, settings)
    conn = (callback.data or "").rsplit(":", 1)[-1]
    data = await state.get_data()
    if conn not in _CONN_KEYS or not data.get("winback_sub"):
        await safe_answer_callback(
            callback, _("error_occurred_try_again"), show_alert=True
        )
        return
    await state.update_data(winback_conn=conn)
    builder = InlineKeyboardBuilder()
    for time_key, label_key in _TIME_KEYS.items():
        builder.button(text=_(label_key), callback_data=f"winback:t:{time_key}")
    builder.adjust(2)
    await _edit_prompt(callback, _("winback_unstable_ask_time"), builder.as_markup())
    await safe_answer_callback(callback)


@router.callback_query(F.data.regexp(r"^winback:t:(morning|day|evening|night)$"))
async def winback_time_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    settings: Settings,
    i18n_data: dict,
) -> None:
    _current_lang, _ = _resolve(i18n_data, settings)
    time_of_day = (callback.data or "").rsplit(":", 1)[-1]
    data = await state.get_data()
    if time_of_day not in _TIME_KEYS or not data.get("winback_sub"):
        await safe_answer_callback(
            callback, _("error_occurred_try_again"), show_alert=True
        )
        return
    await state.update_data(winback_time=time_of_day)
    builder = InlineKeyboardBuilder()
    builder.button(text=_("winback_note_skip"), callback_data="winback:note_skip")
    builder.adjust(1)
    await _edit_prompt(callback, _("winback_unstable_ask_note"), builder.as_markup())
    await state.set_state(WinbackSurveyStates.waiting_for_unstable_note)
    await safe_answer_callback(callback)


async def _finish_unstable(
    *,
    message_or_callback: types.Message | types.CallbackQuery,
    note: str,
    state: FSMContext,
    settings: Settings,
    i18n_data: dict,
    session: AsyncSession,
) -> None:
    _current_lang, _ = _resolve(i18n_data, settings)
    callback: types.CallbackQuery | None = None
    if isinstance(message_or_callback, types.CallbackQuery):
        callback = message_or_callback
        bot = callback.bot
        from_user = callback.from_user
    else:
        bot = message_bot(message_or_callback)
        from_user = message_from_user(message_or_callback)

    data = await state.get_data()
    subscription_id = int(data.get("winback_sub") or 0)
    conn = str(data.get("winback_conn") or "")
    time_of_day = str(data.get("winback_time") or "")
    await state.clear()

    db_user = await user_dal.get_user_by_telegram_id(session, from_user.id)
    if db_user is None or subscription_id <= 0:
        if callback is not None:
            await safe_answer_callback(
                callback, _("error_occurred_try_again"), show_alert=True
            )
        return
    if await survey_already_answered(session, subscription_id):
        if callback is not None:
            await safe_answer_callback(callback, _("winback_already_answered"))
        return

    i18n: JsonI18n | None = i18n_data.get("i18n_instance")
    conn_label = str(i18n.gettext(_current_lang, _CONN_KEYS[conn])) if (
        i18n and conn in _CONN_KEYS
    ) else conn
    time_label = str(i18n.gettext(_current_lang, _TIME_KEYS[time_of_day])) if (
        i18n and time_of_day in _TIME_KEYS
    ) else time_of_day
    reason_text = await _reason_detail("unstable", i18n, _current_lang)

    admin_lines = [reason_text, f"conn={conn_label}", f"time={time_label}"]
    if note:
        admin_lines.append(f"note={note}")
    await _finish_survey(
        session=session,
        subscription_id=subscription_id,
        db_user=db_user,
        audit_content=(
            f"reason=unstable conn={conn} time={time_of_day} note={note or '-'}"
        )[:4000],
        bot=bot,
        settings=settings,
        i18n_data=i18n_data,
        admin_lines=admin_lines,
    )

    if callback is not None:
        await _edit_prompt(callback, _("winback_thanks"))
        await safe_answer_callback(callback)
    elif isinstance(message_or_callback, types.Message):
        await message_or_callback.answer(_("winback_thanks"))


@router.callback_query(
    F.data == "winback:note_skip", WinbackSurveyStates.waiting_for_unstable_note
)
async def winback_note_skip_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    settings: Settings,
    i18n_data: dict,
    session: AsyncSession,
) -> None:
    await _finish_unstable(
        message_or_callback=callback,
        note="",
        state=state,
        settings=settings,
        i18n_data=i18n_data,
        session=session,
    )


@router.message(WinbackSurveyStates.waiting_for_unstable_note, F.text)
async def winback_note_input(
    message: types.Message,
    state: FSMContext,
    settings: Settings,
    i18n_data: dict,
    session: AsyncSession,
) -> None:
    note = (message.text or "").strip()[:MAX_WINBACK_TEXT_LENGTH]
    await _finish_unstable(
        message_or_callback=message,
        note=note,
        state=state,
        settings=settings,
        i18n_data=i18n_data,
        session=session,
    )


@router.message(WinbackSurveyStates.waiting_for_location, F.text)
async def winback_location_input(
    message: types.Message,
    state: FSMContext,
    settings: Settings,
    i18n_data: dict,
    session: AsyncSession,
) -> None:
    current_lang, _ = _resolve(i18n_data, settings)
    location = (message.text or "").strip()[:MAX_WINBACK_TEXT_LENGTH]
    data = await state.get_data()
    subscription_id = int(data.get("winback_sub") or 0)
    await state.clear()

    db_user = await user_dal.get_user_by_telegram_id(
        session, message_from_user(message).id
    )
    if db_user is None or subscription_id <= 0:
        return
    if await survey_already_answered(session, subscription_id):
        return

    i18n: JsonI18n | None = i18n_data.get("i18n_instance")
    reason_text = await _reason_detail("missing_location", i18n, current_lang)
    await _finish_survey(
        session=session,
        subscription_id=subscription_id,
        db_user=db_user,
        audit_content=f"reason=missing_location location={location or '-'}"[:4000],
        bot=message_bot(message),
        settings=settings,
        i18n_data=i18n_data,
        admin_lines=[reason_text, f"location={location}"],
    )
    await message.answer(_("winback_thanks"))
