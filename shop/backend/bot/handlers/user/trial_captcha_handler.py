"""Telegram rendering for the same challenge/proof used by Mini App."""

import base64
import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from bot.middlewares.i18n import JsonI18n
from bot.services.subscription_service_impl.core import SubscriptionService
from bot.services.telegram_account import require_telegram_account_id
from bot.services.trial_captcha import (
    TrialCaptchaError,
    captcha_verified,
    create_trial_challenge,
    verify_trial_challenge,
)
from config.settings import Settings

router = Router(name="trial_captcha")

logger = logging.getLogger(__name__)


class TrialCaptchaState(StatesGroup):
    answer = State()


async def _send_trial_challenge(
    message: types.Message,
    settings: Settings,
    user_id: int,
    i18n: JsonI18n,
    language: str,
    state: FSMContext,
    *,
    auto_activate: bool,
) -> None:
    challenge = await create_trial_challenge(settings, user_id)
    await state.set_state(TrialCaptchaState.answer)
    await state.update_data(
        trial_challenge_id=challenge.challenge_id,
        trial_user_id=user_id,
        trial_auto_activate=auto_activate,
    )
    await message.answer_photo(
        types.BufferedInputFile(base64.b64decode(challenge.image.split(",", 1)[1]), "captcha.png"),
        caption=i18n.gettext(language, "trial_captcha_bot_prompt"),
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text=i18n.gettext(language, "trial_captcha_bot_cancel"),
                        callback_data=f"trial_captcha:cancel:{challenge.challenge_id}",
                    ),
                ]
            ]
        ),
    )


async def ensure_bot_trial_captcha(
    callback: types.CallbackQuery,
    settings: Settings,
    user_id: int,
    i18n: JsonI18n,
    language: str,
    state: FSMContext | None,
    *,
    auto_activate: bool = False,
) -> bool:
    try:
        if await captcha_verified(settings, user_id):
            return True
        if state is None or not isinstance(callback.message, types.Message):
            raise TrialCaptchaError("trial_captcha_unavailable", 503)
        await _send_trial_challenge(
            callback.message,
            settings,
            user_id,
            i18n,
            language,
            state,
            auto_activate=auto_activate,
        )
        await callback.answer()
    except TrialCaptchaError as exc:
        await callback.answer(i18n.gettext(language, exc.code), show_alert=True)
    return False


async def ensure_bot_trial_captcha_message(
    message: types.Message,
    settings: Settings,
    user_id: int,
    i18n: JsonI18n,
    language: str,
    state: FSMContext | None,
) -> bool:
    try:
        if await captcha_verified(settings, user_id):
            return True
        if state is None:
            raise TrialCaptchaError("trial_captcha_unavailable", 503)
        await _send_trial_challenge(
            message, settings, user_id, i18n, language, state, auto_activate=True
        )
    except TrialCaptchaError as exc:
        await message.answer(i18n.gettext(language, exc.code))
    return False


@router.callback_query(F.data.startswith("trial_captcha:cancel:"))
async def cancel_trial_captcha(callback: types.CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    if await state.get_state() == TrialCaptchaState.answer.state and (callback.data or "").rsplit(
        ":", 1
    )[-1] == data.get("trial_challenge_id"):
        await state.clear()
    if isinstance(callback.message, types.Message):
        await callback.message.delete()
    await callback.answer()


@router.message(TrialCaptchaState.answer, F.text)
async def answer_trial_captcha(
    message: types.Message,
    state: FSMContext,
    settings: Settings,
    session: AsyncSession,
    i18n_data: dict,
    subscription_service: SubscriptionService,
) -> None:
    if message.from_user is None:
        return
    i18n: JsonI18n = i18n_data["i18n_instance"]
    language = i18n_data.get("current_language", settings.DEFAULT_LANGUAGE)
    data = await state.get_data()
    try:
        user_id = await require_telegram_account_id(session, message.from_user.id)
    except Exception:
        logger.exception("Failed to resolve account for captcha answer")
        await state.clear()
        await message.answer(i18n.gettext(language, "error_occurred_try_again"))
        return
    await state.clear()
    try:
        if user_id != data.get("trial_user_id"):
            raise TrialCaptchaError("trial_captcha_expired")
        await verify_trial_challenge(
            settings, user_id, str(data.get("trial_challenge_id", "")), message.text or ""
        )
        key = "trial_captcha_bot_success"
    except TrialCaptchaError as exc:
        key = exc.code
    except Exception:
        logger.exception("Unexpected captcha verification error")
        key = "error_occurred_try_again"
    if key == "trial_captcha_bot_success" and data.get("trial_auto_activate"):
        from .trial_handler import try_activate_trial_from_start

        if await try_activate_trial_from_start(
            message,
            settings=settings,
            i18n_data=i18n_data,
            subscription_service=subscription_service,
            session=session,
            state=state,
            user_id=user_id,
        ):
            return
    await message.answer(
        i18n.gettext(language, key),
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text=i18n.gettext(language, "trial_captcha_bot_continue"),
                        callback_data="main_action:request_trial",
                    ),
                ]
            ]
        ),
    )
