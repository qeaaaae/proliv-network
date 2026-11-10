"""User-side no-trial survey flow.

The survey prompt is sent by ``NotrialSurveyWorker`` once a user has been
registered for ``NOTRIAL_MIN_AGE`` without ever getting a subscription.
Reason callbacks ``notrial:r:{reason}:{user_id}``:

- ``no_need`` - record the answer, thank the user;
- ``confusing`` - record and point to the mini-app install flow;
- ``other_vpn`` - mint a personal -10% promo code as a switch incentive;
- ``other`` - ask for a free-text reason.

Every completed answer is recorded in ``message_logs`` (event
``notrial_survey_response``, which doubles as the answered marker) and
forwarded to all admin DMs.
"""

import logging
from collections.abc import Callable
from datetime import datetime
from typing import Any

from aiogram import Bot, F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from bot.middlewares.i18n import JsonI18n
from bot.services.notrial_survey import (
    REASON_LABEL_KEYS,
    find_notrial_promo,
    issue_notrial_discount,
    notify_notrial_admins,
    record_notrial_response,
    survey_already_answered,
)
from bot.services.winback_survey import promo_still_redeemable
from bot.states.user_states import NotrialSurveyStates
from bot.utils.callback_answer import (
    callback_message_or_none,
    message_bot,
    message_from_user,
    safe_answer_callback,
)
from bot.utils.mini_app_url import subscription_mini_app_checkout_code_url
from config.settings import Settings
from db.dal import user_dal
from db.models import User

logger = logging.getLogger(__name__)

router = Router(name="user_notrial_router")

MAX_NOTRIAL_TEXT_LENGTH = 400


def _resolve(i18n_data: dict, settings: Settings) -> tuple[str, Callable[..., str]]:
    current_lang = i18n_data.get("current_language", settings.DEFAULT_LANGUAGE)
    i18n: JsonI18n | None = i18n_data.get("i18n_instance")
    if i18n is None:
        return current_lang, lambda key, **kwargs: key
    return current_lang, lambda key, **kwargs: i18n.gettext(current_lang, key, **kwargs)


async def _edit_prompt(callback: types.CallbackQuery, text: str, markup: Any = None) -> None:
    message = callback_message_or_none(callback)
    if message is None:
        return
    try:
        await message.edit_text(text, reply_markup=markup)
    except Exception:
        logger.warning("Failed to edit no-trial survey message", exc_info=True)


async def _finish_survey(
    *,
    session: AsyncSession,
    db_user: User,
    audit_content: str,
    bot: Bot | None,
    settings: Settings,
    i18n_data: dict,
    admin_lines: list[str],
) -> None:
    await record_notrial_response(session, db_user, content=audit_content)
    await session.commit()
    i18n: JsonI18n | None = i18n_data.get("i18n_instance")
    if i18n is None:
        return
    await notify_notrial_admins(
        bot=bot,
        session=session,
        settings=settings,
        i18n=i18n,
        user=db_user,
        telegram_id=int(getattr(db_user, "telegram_id", 0) or 0),
        detail_lines=admin_lines,
    )


async def _reason_detail(reason: str, i18n: JsonI18n | None, lang: str) -> str:
    label_key = REASON_LABEL_KEYS.get(reason)
    if i18n is None or label_key is None:
        return reason
    return str(i18n.gettext(lang, label_key))


@router.callback_query(F.data.regexp(r"^notrial:r:(no_need|confusing|other_vpn|other):(\d+)$"))
async def notrial_reason_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    settings: Settings,
    i18n_data: dict,
    session: AsyncSession,
) -> None:
    current_lang, _ = _resolve(i18n_data, settings)
    parts = (callback.data or "").split(":")
    if len(parts) != 4:
        await safe_answer_callback(callback, _("error_occurred_try_again"), show_alert=True)
        return
    reason, raw_user_id = parts[2], parts[3]
    try:
        survey_user_id = int(raw_user_id)
    except ValueError:
        await safe_answer_callback(callback, _("error_occurred_try_again"), show_alert=True)
        return

    db_user = await user_dal.get_user_by_telegram_id(session, callback.from_user.id)
    if db_user is None or int(db_user.user_id) != survey_user_id:
        await safe_answer_callback(callback, _("error_occurred_try_again"), show_alert=True)
        return
    if await survey_already_answered(session, int(db_user.user_id)):
        await safe_answer_callback(callback, _("notrial_already_answered"))
        return

    i18n: JsonI18n | None = i18n_data.get("i18n_instance")

    if reason == "no_need":
        reason_text = await _reason_detail(reason, i18n, current_lang)
        await _finish_survey(
            session=session,
            db_user=db_user,
            audit_content="reason=no_need",
            bot=callback.bot,
            settings=settings,
            i18n_data=i18n_data,
            admin_lines=[reason_text],
        )
        await _edit_prompt(callback, _("notrial_thanks"))
        await safe_answer_callback(callback)
        return

    if reason == "confusing":
        reason_text = await _reason_detail(reason, i18n, current_lang)
        await _finish_survey(
            session=session,
            db_user=db_user,
            audit_content="reason=confusing",
            bot=callback.bot,
            settings=settings,
            i18n_data=i18n_data,
            admin_lines=[reason_text],
        )
        builder = InlineKeyboardBuilder()
        mini_app_url = getattr(settings, "SUBSCRIPTION_MINI_APP_URL", "") or ""
        if mini_app_url:
            builder.button(
                text=_("notrial_guide_button"),
                web_app=types.WebAppInfo(url=mini_app_url),
            )
            builder.adjust(1)
        await _edit_prompt(
            callback,
            _("notrial_guide_text"),
            builder.as_markup() if mini_app_url else None,
        )
        await safe_answer_callback(callback)
        return

    if reason == "other_vpn":
        promo = await find_notrial_promo(session, int(db_user.user_id))
        reshow = promo is not None
        if promo is not None and not promo_still_redeemable(promo):
            reason_text = await _reason_detail(reason, i18n, current_lang)
            await _finish_survey(
                session=session,
                db_user=db_user,
                audit_content="reason=other_vpn promo=already_received",
                bot=callback.bot,
                settings=settings,
                i18n_data=i18n_data,
                admin_lines=[reason_text, "promo=already_received"],
            )
            await _edit_prompt(callback, _("notrial_discount_already_received"))
            await safe_answer_callback(callback)
            return
        if promo is None:
            try:
                promo = await issue_notrial_discount(session, db_user)
            except Exception:
                await session.rollback()
                logger.exception("No-trial discount issue failed for user %s", db_user.user_id)
                await safe_answer_callback(callback, _("error_occurred_try_again"), show_alert=True)
                return
        valid_until = getattr(promo, "valid_until", None)
        valid_until_text = (
            valid_until.strftime("%d.%m.%Y") if isinstance(valid_until, datetime) else ""
        )
        reason_text = await _reason_detail(reason, i18n, current_lang)
        suffix = ", re-shown" if reshow else ""
        await _finish_survey(
            session=session,
            db_user=db_user,
            audit_content=(
                f"reason=other_vpn promo={promo.code} discount=10%{' reshow' if reshow else ''}"
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
                text=_("notrial_discount_use_button"),
                web_app=types.WebAppInfo(url=checkout_url),
            )
        mini_app_url = getattr(settings, "SUBSCRIPTION_MINI_APP_URL", "") or ""
        if mini_app_url:
            builder.button(
                text=_("notrial_try_button"),
                web_app=types.WebAppInfo(url=mini_app_url),
            )
        has_buttons = bool(checkout_url or mini_app_url)
        builder.adjust(1)
        await _edit_prompt(
            callback,
            _(
                "notrial_discount_granted",
                code=promo.code,
                discount="10",
                date=valid_until_text,
            ),
            builder.as_markup() if has_buttons else None,
        )
        await safe_answer_callback(callback)
        return

    if reason == "other":
        await state.update_data(notrial_user_id=int(db_user.user_id))
        await state.set_state(NotrialSurveyStates.waiting_for_reason_text)
        await _edit_prompt(callback, _("notrial_ask_other"))
        await safe_answer_callback(callback)
        return

    await safe_answer_callback(callback, _("error_occurred_try_again"), show_alert=True)


@router.message(NotrialSurveyStates.waiting_for_reason_text, F.text)
async def notrial_reason_text_input(
    message: types.Message,
    state: FSMContext,
    settings: Settings,
    i18n_data: dict,
    session: AsyncSession,
) -> None:
    current_lang, _ = _resolve(i18n_data, settings)
    note = (message.text or "").strip()[:MAX_NOTRIAL_TEXT_LENGTH]
    data = await state.get_data()
    survey_user_id = int(data.get("notrial_user_id") or 0)
    await state.clear()

    db_user = await user_dal.get_user_by_telegram_id(session, message_from_user(message).id)
    if db_user is None or int(db_user.user_id) != survey_user_id:
        return
    if await survey_already_answered(session, int(db_user.user_id)):
        return

    i18n: JsonI18n | None = i18n_data.get("i18n_instance")
    reason_text = await _reason_detail("other", i18n, current_lang)
    await _finish_survey(
        session=session,
        db_user=db_user,
        audit_content=f"reason=other note={note or '-'}"[:4000],
        bot=message_bot(message),
        settings=settings,
        i18n_data=i18n_data,
        admin_lines=[reason_text, f"note={note}"],
    )
    await message.answer(_("notrial_thanks"))
