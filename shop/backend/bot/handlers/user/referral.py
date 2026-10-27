import logging
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote
from uuid import uuid4

from aiogram import Bot, F, Router, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from bot.middlewares.i18n import JsonI18n
from bot.services.partner_common import (
    amount_to_minor,
    currency_scale,
    minor_to_decimal_string,
)
from bot.services.partner_program_service import PartnerProgramService
from bot.services.referral_service import ReferralService
from bot.services.subscription_service_impl.core import SubscriptionService
from bot.services.telegram_account import require_telegram_account_id
from bot.utils.callback_answer import callback_data, message_from_user
from bot.utils.custom_emoji import custom_emoji_unicode_html
from config.settings import Settings
from db.dal import user_balance_dal, user_dal

from .menu_card import render_card, send_card

logger = logging.getLogger(__name__)

router = Router(name="user_referral_router")

Translator = Callable[..., str]


async def referral_command_handler(
    event: types.Message | types.CallbackQuery,
    settings: Settings,
    i18n_data: dict,
    referral_service: ReferralService,
    bot: Bot,
    session: AsyncSession,
    back_callback: str = "main_action:back_to_main",
) -> None:
    current_lang = i18n_data.get("current_language", settings.DEFAULT_LANGUAGE)
    i18n: JsonI18n | None = i18n_data.get("i18n_instance")

    target_message_obj = event.message if isinstance(event, types.CallbackQuery) else event
    if not target_message_obj:
        logger.error(
            "Target message is None in referral_command_handler (possibly from callback without message)."  # noqa: E501
        )
        if isinstance(event, types.CallbackQuery):
            await event.answer("Error displaying referral info.", show_alert=True)
        return

    if not i18n or not referral_service:
        logger.error("Dependencies (i18n or ReferralService) missing in referral_command_handler")
        await target_message_obj.answer("Service error. Please try again later.")
        if isinstance(event, types.CallbackQuery):
            await event.answer()
        return

    _ = lambda key, **kwargs: i18n.gettext(current_lang, key, **kwargs)

    inviter_user_id = (
        await require_telegram_account_id(session, event.from_user.id)
        if isinstance(event, types.CallbackQuery)
        else await require_telegram_account_id(session, message_from_user(event).id)
    )
    referral_program_enabled = await PartnerProgramService(
        settings
    ).referral_program_enabled_for_user(
        session,
        user_id=inviter_user_id,
    )
    if not referral_program_enabled:
        await target_message_obj.answer(_("referral_program_unavailable_for_partner"))
        if isinstance(event, types.CallbackQuery):
            await event.answer()
        return

    try:
        bot_info = await bot.get_me()
        bot_username = bot_info.username
    except Exception as e_bot_info:
        logger.error("Failed to get bot info for referral link: %s", e_bot_info)
        await target_message_obj.answer(_("error_generating_referral_link"))
        if isinstance(event, types.CallbackQuery):
            await event.answer()
        return

    if not bot_username:
        logger.error("Bot username is None, cannot generate referral link.")
        await target_message_obj.answer(_("error_generating_referral_link"))
        if isinstance(event, types.CallbackQuery):
            await event.answer()
        return

    referral_link = await referral_service.generate_referral_link(
        session, bot_username, inviter_user_id
    )

    if not referral_link:
        logger.error(
            "Failed to generate referral link for user %s (probably missing DB record).",
            inviter_user_id,
        )
        await target_message_obj.answer(_("error_generating_referral_link"))
        if isinstance(event, types.CallbackQuery):
            await event.answer()
        return

    if settings.traffic_sale_mode:
        bonus_details_str = _("referral_not_available_for_traffic")
    else:
        bonus_details_str = _build_referral_bonus_details_text(settings, _, current_lang)

    referral_stats = await referral_service.get_referral_stats(session, inviter_user_id)

    text = _(
        "referral_program_info_new",
        bonus_details=bonus_details_str,
        invited_count=referral_stats["invited_count"],
        purchased_count=referral_stats["purchased_count"],
    )

    from bot.keyboards.inline.user_keyboards import get_referral_link_keyboard

    share_text = custom_emoji_unicode_html(_("referral_share_intro"))
    share_url = f"https://t.me/share/url?url={quote(referral_link)}&text={quote(share_text)}"

    reply_markup_val = get_referral_link_keyboard(
        current_lang,
        i18n,
        back_callback=back_callback,
        referral_info_url=settings.REFERRAL_INFO_URL,
        exchange_enabled=bool(settings.BONUS_EXCHANGE_DAY_PRICE),
        share_url=share_url,
        referral_link=referral_link,
    )

    if isinstance(event, types.Message):
        await send_card(
            bot,
            event.chat.id,
            text,
            reply_markup_val,
            disable_web_page_preview=True,
        )
    elif isinstance(event, types.CallbackQuery) and event.message:
        await render_card(event, text, reply_markup_val, disable_web_page_preview=True)
        await event.answer()


@router.callback_query(F.data.startswith("referral_action:"))
async def referral_action_handler(
    callback: types.CallbackQuery,
    settings: Settings,
    i18n_data: dict,
    referral_service: ReferralService,
    bot: Bot,
    session: AsyncSession,
    subscription_service: SubscriptionService,
) -> None:
    action = callback_data(callback).split(":")[1]
    current_lang = i18n_data.get("current_language", settings.DEFAULT_LANGUAGE)
    i18n: JsonI18n | None = i18n_data.get("i18n_instance")
    if not i18n:
        await callback.answer("Language service error.", show_alert=True)
        return
    _ = lambda key, **kwargs: i18n.gettext(current_lang, key, **kwargs)

    referral_program_enabled = await PartnerProgramService(
        settings
    ).referral_program_enabled_for_user(
        session,
        user_id=await require_telegram_account_id(session, callback.from_user.id),
    )
    if not referral_program_enabled:
        await callback.answer(_("referral_program_unavailable_for_partner"), show_alert=True)
        return

    if action == "back":
        await referral_command_handler(
            callback, settings, i18n_data, referral_service, bot, session
        )
        return

    elif action == "exchange":
        await _render_exchange_screen(callback, settings, _, session)

    elif action == "exchange_confirm":
        await _handle_exchange_confirm(callback, settings, _, session, subscription_service)
        return

    await callback.answer()


async def _exchange_context(
    settings: Settings, session: AsyncSession, user_id: int
) -> tuple[str, int, int, int] | None:
    price = settings.BONUS_EXCHANGE_DAY_PRICE
    if not price or price <= 0:
        return None
    currency = settings.balance_settings.currency
    scale = currency_scale(currency)
    price_minor = amount_to_minor(price, scale=scale)
    if price_minor <= 0:
        return None
    balance_minor = await user_balance_dal.balance_minor(session, user_id, currency)
    return currency, scale, price_minor, balance_minor


async def _render_exchange_screen(
    callback: types.CallbackQuery,
    settings: Settings,
    gettext: Translator,
    session: AsyncSession,
) -> None:
    user_id = await require_telegram_account_id(session, callback.from_user.id)
    context = await _exchange_context(settings, session, user_id)
    if context is None:
        await callback.answer(gettext("referral_exchange_unavailable"), show_alert=True)
        return
    currency, scale, price_minor, balance_minor = context
    days = balance_minor // price_minor

    text = gettext(
        "referral_exchange_screen",
        price=minor_to_decimal_string(price_minor, scale=scale),
        currency=currency,
        balance=minor_to_decimal_string(balance_minor, scale=scale),
        days=days,
    )
    if days < 1:
        text = f"{text}\n\n{gettext('referral_exchange_insufficient')}"

    builder = InlineKeyboardBuilder()
    if days >= 1:
        builder.row(
            InlineKeyboardButton(
                text=gettext("referral_exchange_do_button"),
                callback_data="referral_action:exchange_confirm",
            )
        )
    builder.row(
        InlineKeyboardButton(
            text=gettext("wa_back"),
            callback_data="referral_action:back",
        )
    )
    await render_card(callback, text, builder.as_markup())


async def _handle_exchange_confirm(
    callback: types.CallbackQuery,
    settings: Settings,
    gettext: Translator,
    session: AsyncSession,
    subscription_service: SubscriptionService,
) -> None:
    user_id = await require_telegram_account_id(session, callback.from_user.id)
    await user_dal.lock_user_by_id(session, user_id)

    context = await _exchange_context(settings, session, user_id)
    if context is None:
        await callback.answer(gettext("referral_exchange_unavailable"), show_alert=True)
        return
    currency, scale, price_minor, balance_minor = context
    days = int(balance_minor // price_minor)
    if days <= 0:
        await callback.answer(gettext("referral_exchange_insufficient"), show_alert=True)
        return

    spend_minor = days * price_minor
    exchange_id = uuid4().hex
    await user_balance_dal.create_ledger_entry(
        session,
        user_id=user_id,
        currency=currency,
        currency_scale=scale,
        amount_minor=-spend_minor,
        kind="extension_purchase",
        state="posted",
        reference_type="bonus_exchange",
        reference_id=f"bonus-exchange:{user_id}:{exchange_id[:16]}",
        idempotency_key=f"bonus-exchange:{exchange_id}",
        reason="bonus balance exchange to subscription days",
        posted_at=datetime.now(UTC),
    )
    try:
        new_end_date = await subscription_service.extend_active_subscription_days(
            session,
            user_id=user_id,
            bonus_days=days,
            reason="bonus exchange",
        )
    except Exception:
        logger.exception("Bonus exchange failed while extending user %s.", user_id)
        await session.rollback()
        await callback.answer(gettext("referral_exchange_failed"), show_alert=True)
        return
    if not new_end_date:
        await session.rollback()
        await callback.answer(gettext("referral_exchange_failed"), show_alert=True)
        return
    await session.commit()

    text = gettext(
        "referral_exchange_success",
        amount=minor_to_decimal_string(spend_minor, scale=scale),
        currency=currency,
        days=days,
        end_date=new_end_date.strftime("%d.%m.%Y"),
    )
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=gettext("wa_back"),
            callback_data="referral_action:back",
        )
    )
    await render_card(callback, text, builder.as_markup())
    await callback.answer()


def _period_bonus_text(
    translator: Translator,
    *,
    months: int,
    inviter_days: int | None,
    referee_days: int | None,
) -> str:
    return translator(
        "referral_bonus_per_period",
        months=months,
        inviter_bonus_days=(
            inviter_days if inviter_days is not None else translator("no_bonus_placeholder")
        ),
        referee_bonus_days=(
            referee_days if referee_days is not None else translator("no_bonus_placeholder")
        ),
    )


def _tariff_period_bonus_entries(tariff: Any) -> list[dict[str, int | None]]:
    entries: list[dict[str, int | None]] = []
    for months in sorted(int(month) for month in getattr(tariff, "enabled_periods", [])):
        inviter_days = tariff.referral_inviter_bonus_days(months)
        referee_days = tariff.referral_referee_bonus_days(months)
        if inviter_days is None and referee_days is None:
            continue
        entries.append(
            {
                "months": months,
                "inviter_days": inviter_days,
                "referee_days": referee_days,
            }
        )
    return entries


def _legacy_period_bonus_entries(settings: Settings) -> list[dict[str, int | None]]:
    entries: list[dict[str, int | None]] = []
    for months, _price in sorted(settings.subscription_options.items()):
        inviter_days = settings.referral_bonus_inviter.get(months)
        referee_days = settings.referral_bonus_referee.get(months)
        if inviter_days is None and referee_days is None:
            continue
        entries.append(
            {
                "months": int(months),
                "inviter_days": inviter_days,
                "referee_days": referee_days,
            }
        )
    return entries


def _bonus_days_range(translator: Translator, values: list[int]) -> str:
    return translator(
        "referral_bonus_days_range",
        min_days=min(values),
        max_days=max(values),
    )


def _build_referral_bonus_details_text(
    settings: Settings, translator: Translator, current_lang: str
) -> str:
    tariffs_config = settings.tariffs_config
    if not tariffs_config:
        bonus_info_parts = [
            _period_bonus_text(
                translator,
                months=int(entry["months"] or 0),
                inviter_days=entry["inviter_days"],
                referee_days=entry["referee_days"],
            )
            for entry in _legacy_period_bonus_entries(settings)
        ]
        return (
            "\n".join(bonus_info_parts)
            if bonus_info_parts
            else translator("referral_no_bonuses_configured")
        )

    period_tariffs = [
        tariff for tariff in tariffs_config.enabled_tariffs if tariff.billing_model == "period"
    ]
    if len(period_tariffs) <= 1:
        entries = _tariff_period_bonus_entries(period_tariffs[0]) if period_tariffs else []
        bonus_info_parts = [
            _period_bonus_text(
                translator,
                months=int(entry["months"] or 0),
                inviter_days=entry["inviter_days"],
                referee_days=entry["referee_days"],
            )
            for entry in entries
        ]
        return (
            "\n".join(bonus_info_parts)
            if bonus_info_parts
            else translator("referral_no_bonuses_configured")
        )

    bonus_info_parts = []
    for tariff in period_tariffs:
        entries = _tariff_period_bonus_entries(tariff)
        if not entries:
            continue
        inviter_values = [int(entry["inviter_days"] or 0) for entry in entries]
        referee_values = [int(entry["referee_days"] or 0) for entry in entries]
        bonus_info_parts.append(
            translator(
                "referral_bonus_tariff_range",
                tariff_name=tariff.name(current_lang),
                inviter_bonus_range=_bonus_days_range(translator, inviter_values),
                referee_bonus_range=_bonus_days_range(translator, referee_values),
            )
        )
    return (
        "\n".join(bonus_info_parts)
        if bonus_info_parts
        else translator("referral_no_bonuses_configured")
    )


@router.message(Command("referral"))
async def referral_command_message_handler(
    message: types.Message,
    settings: Settings,
    i18n_data: dict,
    referral_service: ReferralService,
    bot: Bot,
    session: AsyncSession,
) -> None:
    await referral_command_handler(message, settings, i18n_data, referral_service, bot, session)
