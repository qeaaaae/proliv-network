import contextlib
import logging

from aiogram import types
from aiogram.utils.text_decorations import html_decoration as hd
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline.user_keyboards import (
    get_bot_interface_inline_keyboard,
    get_main_menu_inline_keyboard,
)
from bot.middlewares.i18n import JsonI18n
from bot.services.partner_common import currency_scale, minor_to_decimal_string
from bot.services.partner_program_service import PartnerProgramService
from bot.services.subscription_service_impl.core import SubscriptionService
from bot.services.telegram_account import require_telegram_account_id
from bot.utils.callback_answer import (
    callback_message,
    message_from_user,
    safe_answer_callback,
)
from config.settings import Settings
from db.dal import partner_dal, subscription_dal, user_balance_dal

from .menu_card import render_card

logger = logging.getLogger(__name__)


async def should_show_trial_button(
    settings: Settings,
    subscription_service: SubscriptionService,
    session: AsyncSession,
    user_id: int,
) -> bool:
    if not settings.TRIAL_ENABLED:
        return False

    if hasattr(subscription_service, "has_trial_blocking_subscription") and callable(
        subscription_service.has_trial_blocking_subscription
    ):
        return not await subscription_service.has_trial_blocking_subscription(session, user_id)

    logger.error("Method has_trial_blocking_subscription is missing in SubscriptionService!")
    return False


async def send_main_menu(
    target_event: types.Message | types.CallbackQuery,
    settings: Settings,
    i18n_data: dict,
    subscription_service: SubscriptionService,
    session: AsyncSession,
    is_edit: bool = False,
) -> None:
    current_lang = i18n_data.get("current_language", settings.DEFAULT_LANGUAGE)
    i18n: JsonI18n | None = i18n_data.get("i18n_instance")

    event_user = (
        target_event.from_user
        if isinstance(target_event, types.CallbackQuery)
        else message_from_user(target_event)
    )
    user_id = await require_telegram_account_id(session, event_user.id)
    user_full_name = hd.quote(event_user.full_name)

    if not i18n:
        logger.error("i18n_instance missing in send_main_menu for user %s", user_id)
        err_msg_fallback = "Error: Language service unavailable. Please try again later."
        if isinstance(target_event, types.CallbackQuery):
            with contextlib.suppress(Exception):
                await target_event.answer(err_msg_fallback, show_alert=True)
        elif isinstance(target_event, types.Message):
            with contextlib.suppress(Exception):
                await target_event.answer(err_msg_fallback)
        return

    _ = lambda key, **kwargs: i18n.gettext(current_lang, key, **kwargs)

    show_trial_button_in_menu = await should_show_trial_button(
        settings, subscription_service, session, user_id
    )

    currency = settings.balance_settings.currency
    balance_minor = await user_balance_dal.balance_minor(session, user_id, currency)
    # Vendored-патч: в главном меню «Бонусы» показываем сумму бонусного и
    # партнёрского кошельков - в кабинете карточка «Бонусный счёт» считает так же.
    partner_profile = None
    if settings.partner_settings.enabled:
        partner_profile = await partner_dal.get_profile_by_user_id(session, user_id)
        if partner_profile is not None:
            balance_minor += await partner_dal.balance_minor(
                session, int(partner_profile.partner_id), currency
            )
    balance_text = minor_to_decimal_string(
        balance_minor, scale=currency_scale(currency)
    ).rstrip("0").rstrip(".")
    currency_display = "₽" if currency.upper() == "RUB" else currency

    active_sub = await subscription_dal.get_active_subscription_by_user_id(session, user_id)
    if active_sub is not None and active_sub.end_date:
        status_block = _(
            "main_menu_sub_active", end_date=active_sub.end_date.strftime("%d.%m.%Y")
        )
    else:
        status_block = _("main_menu_sub_expired")

    streamer_line = (
        f"\n\n{_('main_menu_streamer_badge')}"
        if partner_profile is not None
        and str(getattr(partner_profile, "kind", "standard") or "standard") == "streamer"
        else ""
    )
    account_block = _(
        "main_menu_account_block",
        user_id=event_user.id,
        balance=balance_text,
        currency=currency_display,
    )
    text = (
        f"{_(key='main_menu_greeting', user_name=user_full_name)}\n\n"
        f"{account_block}\n\n"
        f"{status_block}{streamer_line}"
    )
    reply_markup = get_main_menu_inline_keyboard(
        current_lang,
        i18n,
        settings,
        show_trial_button_in_menu,
        user_id=user_id,
    )

    target_message_obj: types.Message | None = None
    if isinstance(target_event, types.Message):
        target_message_obj = target_event
    elif isinstance(target_event, types.CallbackQuery) and target_event.message:
        target_message_obj = callback_message(target_event)

    if not target_message_obj:
        logger.error("send_main_menu: target_message_obj is None for event from user %s.", user_id)
        if isinstance(target_event, types.CallbackQuery):
            await safe_answer_callback(
                target_event,
                _("error_displaying_menu"),
                show_alert=True,
            )
        return

    try:
        await render_card(target_event, text, reply_markup, is_edit=is_edit)
        if isinstance(target_event, types.CallbackQuery):
            await safe_answer_callback(target_event)
    except Exception as e_send_edit:
        logger.warning(
            "Failed to send/edit main menu (user: %s, is_edit: %s): %s - %s.",
            user_id,
            is_edit,
            type(e_send_edit).__name__,
            e_send_edit,
        )
        if isinstance(target_event, types.CallbackQuery):
            await safe_answer_callback(
                target_event,
                _("error_occurred_try_again") if is_edit else None,
            )


async def send_bot_interface_menu(
    target_event: types.Message | types.CallbackQuery,
    settings: Settings,
    i18n_data: dict,
    subscription_service: SubscriptionService,
    session: AsyncSession,
    is_edit: bool = False,
) -> None:
    current_lang = i18n_data.get("current_language", settings.DEFAULT_LANGUAGE)
    i18n: JsonI18n | None = i18n_data.get("i18n_instance")

    if not i18n:
        logger.error("i18n_instance missing in send_bot_interface_menu.")
        return

    event_user = (
        target_event.from_user
        if isinstance(target_event, types.CallbackQuery)
        else message_from_user(target_event)
    )
    user_id = await require_telegram_account_id(session, event_user.id)
    show_trial_button_in_menu = await should_show_trial_button(
        settings, subscription_service, session, user_id
    )
    referral_program_enabled = await PartnerProgramService(
        settings
    ).referral_program_enabled_for_user(
        session,
        user_id=user_id,
    )

    text = i18n.gettext(current_lang, "bot_interface_menu_title")
    if settings.SUBSCRIPTION_MINI_APP_URL:
        text = f"{text}\n\n{i18n.gettext(current_lang, 'bot_interface_menu_webapp_hint')}"
    reply_markup = get_bot_interface_inline_keyboard(
        current_lang,
        i18n,
        settings,
        show_trial_button_in_menu,
        referral_program_enabled=referral_program_enabled,
    )

    target_message_obj: types.Message | None = None
    if isinstance(target_event, types.Message):
        target_message_obj = target_event
    elif isinstance(target_event, types.CallbackQuery) and target_event.message:
        target_message_obj = callback_message(target_event)

    if not target_message_obj:
        logger.error(
            "send_bot_interface_menu: target_message_obj is None for user %s.",
            user_id,
        )
        return

    try:
        await render_card(target_event, text, reply_markup, is_edit=is_edit)
        if isinstance(target_event, types.CallbackQuery):
            await safe_answer_callback(target_event)
    except Exception as e_send_edit:
        logger.warning(
            "Failed to send/edit bot interface menu (user: %s, is_edit: %s): %s - %s.",
            user_id,
            is_edit,
            type(e_send_edit).__name__,
            e_send_edit,
        )
