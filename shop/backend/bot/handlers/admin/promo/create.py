import logging
import re
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from aiogram import F, Router, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline.admin_keyboards import (
    get_admin_panel_keyboard,
    get_back_to_admin_panel_keyboard,
)
from bot.middlewares.i18n import JsonI18n
from bot.services.promo_code_service import PromoCodeService
from bot.services.promo_effects import PROMO_APPLIES_TO_SUBSCRIPTION, PromoEffects
from bot.states.admin_states import AdminStates
from bot.utils.callback_answer import callback_message
from config.settings import Settings
from db.dal import promo_code_dal

logger = logging.getLogger(__name__)

router = Router(name="promo_create_router")

_PROMO_CODE_RE = re.compile(r"[A-Za-z0-9_-]{3,30}")


def _promo_effect_label(gettext: Callable[..., str], data: dict[str, Any]) -> str:
    if data.get("discount_percent") is not None:
        return gettext("admin_promo_effect_discount_value", value=data["discount_percent"])
    return gettext("admin_promo_effect_bonus_days_value", value=data.get("bonus_days") or 0)


async def create_promo_prompt_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    i18n_data: dict,
    settings: Settings,
    session: AsyncSession,
) -> None:
    current_lang = i18n_data.get("current_language", settings.DEFAULT_LANGUAGE)
    i18n: JsonI18n | None = i18n_data.get("i18n_instance")
    if not i18n or not callback.message:
        await callback.answer("Error preparing promo creation.", show_alert=True)
        return
    _ = lambda key, **kwargs: i18n.gettext(current_lang, key, **kwargs)

    # Step 1: Ask for promo code
    prompt_text = _("admin_promo_step1_code")

    try:
        await callback_message(callback).edit_text(
            prompt_text,
            reply_markup=get_back_to_admin_panel_keyboard(current_lang, i18n),
            parse_mode="HTML",
        )
    except Exception as e:
        logger.warning("Could not edit message for promo prompt: %s. Sending new.", e)
        await callback_message(callback).answer(
            prompt_text,
            reply_markup=get_back_to_admin_panel_keyboard(current_lang, i18n),
            parse_mode="HTML",
        )
    await callback.answer()
    await state.set_state(AdminStates.waiting_for_promo_code)


# Step 1: Process promo code
@router.message(AdminStates.waiting_for_promo_code, F.text)
async def process_promo_code_handler(
    message: types.Message,
    state: FSMContext,
    i18n_data: dict,
    settings: Settings,
    session: AsyncSession,
) -> None:
    current_lang = i18n_data.get("current_language", settings.DEFAULT_LANGUAGE)
    i18n: JsonI18n | None = i18n_data.get("i18n_instance")
    if not i18n:
        await message.reply("Language service error.")
        return
    _ = lambda key, **kwargs: i18n.gettext(current_lang, key, **kwargs)

    try:
        code_str = (message.text or "").strip().upper()
        if not _PROMO_CODE_RE.fullmatch(code_str):
            await message.answer(_("admin_promo_invalid_code_format"))
            return

        # Check if code already exists
        existing_promo = await promo_code_dal.get_promo_code_by_code(session, code_str)
        if existing_promo and getattr(existing_promo, "archived_at", None) is not None:
            await promo_code_dal.release_archived_promo_code(session, existing_promo)
            await session.commit()
            existing_promo = None
        if existing_promo:
            await message.answer(_("admin_promo_code_already_exists"))
            return

        await state.update_data(promo_code=code_str)

        # Step 2: Choose promo type
        prompt_text = _("admin_promo_step2_type", code=code_str)

        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text=_("admin_promo_type_bonus_days_button"),
                callback_data="promo_type:bonus_days",
            ),
            InlineKeyboardButton(
                text=_("admin_promo_type_discount_button"),
                callback_data="promo_type:discount",
            ),
        )
        builder.row(
            InlineKeyboardButton(text=_("admin_back_to_panel"), callback_data="admin_action:main")
        )

        await message.answer(prompt_text, reply_markup=builder.as_markup(), parse_mode="HTML")
        await state.set_state(AdminStates.waiting_for_promo_type)

    except Exception as e:
        logger.error("Error processing promo code: %s", e)
        await message.answer(_("error_occurred_try_again"))


# Step 2: Process type selection
@router.callback_query(
    F.data == "promo_type:bonus_days", StateFilter(AdminStates.waiting_for_promo_type)
)
async def process_promo_type_bonus_days(
    callback: types.CallbackQuery, state: FSMContext, i18n_data: dict, settings: Settings
) -> None:
    current_lang = i18n_data.get("current_language", settings.DEFAULT_LANGUAGE)
    i18n: JsonI18n | None = i18n_data.get("i18n_instance")
    if not i18n or not callback.message:
        await callback.answer("Error processing promo type.", show_alert=True)
        return
    _ = lambda key, **kwargs: i18n.gettext(current_lang, key, **kwargs)

    await state.update_data(promo_type="bonus_days", discount_percent=None)
    data = await state.get_data()
    prompt_text = _("admin_promo_step3_bonus_days", code=data.get("promo_code"))

    try:
        await callback_message(callback).edit_text(
            prompt_text,
            reply_markup=get_back_to_admin_panel_keyboard(current_lang, i18n),
            parse_mode="HTML",
        )
    except Exception:
        await callback_message(callback).answer(
            prompt_text,
            reply_markup=get_back_to_admin_panel_keyboard(current_lang, i18n),
            parse_mode="HTML",
        )
    await callback.answer()
    await state.set_state(AdminStates.waiting_for_promo_bonus_days)


@router.callback_query(
    F.data == "promo_type:discount", StateFilter(AdminStates.waiting_for_promo_type)
)
async def process_promo_type_discount(
    callback: types.CallbackQuery, state: FSMContext, i18n_data: dict, settings: Settings
) -> None:
    current_lang = i18n_data.get("current_language", settings.DEFAULT_LANGUAGE)
    i18n: JsonI18n | None = i18n_data.get("i18n_instance")
    if not i18n or not callback.message:
        await callback.answer("Error processing promo type.", show_alert=True)
        return
    _ = lambda key, **kwargs: i18n.gettext(current_lang, key, **kwargs)

    await state.update_data(promo_type="discount", bonus_days=0)
    data = await state.get_data()
    prompt_text = _("admin_promo_step3_discount", code=data.get("promo_code"))

    try:
        await callback_message(callback).edit_text(
            prompt_text,
            reply_markup=get_back_to_admin_panel_keyboard(current_lang, i18n),
            parse_mode="HTML",
        )
    except Exception:
        await callback_message(callback).answer(
            prompt_text,
            reply_markup=get_back_to_admin_panel_keyboard(current_lang, i18n),
            parse_mode="HTML",
        )
    await callback.answer()
    await state.set_state(AdminStates.waiting_for_promo_discount)


# Step 3: Process bonus days
@router.message(AdminStates.waiting_for_promo_bonus_days, F.text)
async def process_promo_bonus_days_handler(
    message: types.Message, state: FSMContext, i18n_data: dict, settings: Settings
) -> None:
    current_lang = i18n_data.get("current_language", settings.DEFAULT_LANGUAGE)
    i18n: JsonI18n | None = i18n_data.get("i18n_instance")
    if not i18n:
        await message.reply("Language service error.")
        return
    _ = lambda key, **kwargs: i18n.gettext(current_lang, key, **kwargs)

    try:
        bonus_days = int((message.text or "").strip())
        if not (1 <= bonus_days <= 365):
            await message.answer(_("admin_promo_invalid_bonus_days"))
            return

        await state.update_data(bonus_days=bonus_days)
        await _prompt_max_activations(message, state, i18n_data, settings)

    except ValueError:
        await message.answer(_("admin_promo_invalid_number"))
    except Exception as e:
        logger.error("Error processing promo bonus days: %s", e)
        await message.answer(_("error_occurred_try_again"))


# Step 3: Process discount percent
@router.message(AdminStates.waiting_for_promo_discount, F.text)
async def process_promo_discount_handler(
    message: types.Message, state: FSMContext, i18n_data: dict, settings: Settings
) -> None:
    current_lang = i18n_data.get("current_language", settings.DEFAULT_LANGUAGE)
    i18n: JsonI18n | None = i18n_data.get("i18n_instance")
    if not i18n:
        await message.reply("Language service error.")
        return
    _ = lambda key, **kwargs: i18n.gettext(current_lang, key, **kwargs)

    try:
        discount = float((message.text or "").strip().replace(",", "."))
        if not (0 < discount <= 100):
            await message.answer(_("admin_promo_invalid_discount"))
            return
        if discount.is_integer():
            discount = int(discount)

        await state.update_data(discount_percent=discount)
        await _prompt_max_activations(message, state, i18n_data, settings)

    except ValueError:
        await message.answer(_("admin_promo_invalid_discount"))
    except Exception as e:
        logger.error("Error processing promo discount: %s", e)
        await message.answer(_("error_occurred_try_again"))


async def _prompt_max_activations(
    message: types.Message, state: FSMContext, i18n_data: dict, settings: Settings
) -> None:
    """Step 4: ask for max activations (shared by bonus-days and discount paths)."""
    current_lang = i18n_data.get("current_language", settings.DEFAULT_LANGUAGE)
    i18n: JsonI18n | None = i18n_data.get("i18n_instance")
    if not i18n:
        return
    _ = lambda key, **kwargs: i18n.gettext(current_lang, key, **kwargs)

    data = await state.get_data()
    prompt_text = _(
        "admin_promo_step4_max_activations",
        code=data.get("promo_code"),
        effect=_promo_effect_label(_, data),
    )

    await message.answer(
        prompt_text,
        reply_markup=get_back_to_admin_panel_keyboard(current_lang, i18n),
        parse_mode="HTML",
    )
    await state.set_state(AdminStates.waiting_for_promo_max_activations)


# Step 4: Process max activations
@router.message(AdminStates.waiting_for_promo_max_activations, F.text)
async def process_promo_max_activations_handler(
    message: types.Message, state: FSMContext, i18n_data: dict, settings: Settings
) -> None:
    current_lang = i18n_data.get("current_language", settings.DEFAULT_LANGUAGE)
    i18n: JsonI18n | None = i18n_data.get("i18n_instance")
    if not i18n:
        await message.reply("Language service error.")
        return
    _ = lambda key, **kwargs: i18n.gettext(current_lang, key, **kwargs)

    try:
        max_activations = int((message.text or "").strip())
        if not (1 <= max_activations <= 10000):
            await message.answer(_("admin_promo_invalid_max_activations"))
            return

        await state.update_data(max_activations=max_activations)

        # Step 5: Ask for validity
        data = await state.get_data()
        prompt_text = _(
            "admin_promo_step5_validity",
            code=data.get("promo_code"),
            effect=_promo_effect_label(_, data),
            max_activations=max_activations,
        )

        # Create keyboard for validity options
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text=_("admin_promo_unlimited_validity"), callback_data="promo_unlimited_validity"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text=_("admin_promo_set_validity_days"), callback_data="promo_set_validity"
            )
        )
        builder.row(
            InlineKeyboardButton(text=_("admin_back_to_panel"), callback_data="admin_action:main")
        )

        await message.answer(prompt_text, reply_markup=builder.as_markup(), parse_mode="HTML")
        await state.set_state(AdminStates.waiting_for_promo_validity_days)

    except ValueError:
        await message.answer(_("admin_promo_invalid_number"))
    except Exception as e:
        logger.error("Error processing promo max activations: %s", e)
        await message.answer(_("error_occurred_try_again"))


# Step 5: Handle unlimited validity
@router.callback_query(
    F.data == "promo_unlimited_validity", StateFilter(AdminStates.waiting_for_promo_validity_days)
)
async def process_promo_unlimited_validity(
    callback: types.CallbackQuery,
    state: FSMContext,
    i18n_data: dict,
    settings: Settings,
    session: AsyncSession,
) -> None:
    await state.update_data(validity_days=None)
    await create_promo_code_final(callback, state, i18n_data, settings, session)


# Step 5: Handle set validity
@router.callback_query(
    F.data == "promo_set_validity", StateFilter(AdminStates.waiting_for_promo_validity_days)
)
async def process_promo_set_validity(
    callback: types.CallbackQuery, state: FSMContext, i18n_data: dict, settings: Settings
) -> None:
    current_lang = i18n_data.get("current_language", settings.DEFAULT_LANGUAGE)
    i18n: JsonI18n | None = i18n_data.get("i18n_instance")
    if not i18n or not callback.message:
        await callback.answer("Error processing validity.", show_alert=True)
        return
    _ = lambda key, **kwargs: i18n.gettext(current_lang, key, **kwargs)

    data = await state.get_data()
    prompt_text = _(
        "admin_promo_enter_validity_days",
        code=data.get("promo_code"),
        effect=_promo_effect_label(_, data),
        max_activations=data.get("max_activations"),
    )

    try:
        await callback_message(callback).edit_text(
            prompt_text,
            reply_markup=get_back_to_admin_panel_keyboard(current_lang, i18n),
            parse_mode="HTML",
        )
    except Exception:
        await callback_message(callback).answer(
            prompt_text,
            reply_markup=get_back_to_admin_panel_keyboard(current_lang, i18n),
            parse_mode="HTML",
        )
    await callback.answer()


# Step 5: Process validity days
@router.message(AdminStates.waiting_for_promo_validity_days, F.text)
async def process_promo_validity_days_handler(
    message: types.Message,
    state: FSMContext,
    i18n_data: dict,
    settings: Settings,
    session: AsyncSession,
) -> None:
    current_lang = i18n_data.get("current_language", settings.DEFAULT_LANGUAGE)
    i18n: JsonI18n | None = i18n_data.get("i18n_instance")
    if not i18n:
        await message.reply("Language service error.")
        return
    _ = lambda key, **kwargs: i18n.gettext(current_lang, key, **kwargs)

    try:
        validity_days = int((message.text or "").strip())
        if not (1 <= validity_days <= 365):
            await message.answer(_("admin_promo_invalid_validity_days"))
            return

        await state.update_data(validity_days=validity_days)
        await create_promo_code_final(message, state, i18n_data, settings, session)

    except ValueError:
        await message.answer(_("admin_promo_invalid_number"))
    except Exception as e:
        logger.error("Error processing promo validity days: %s", e)
        await message.answer(_("error_occurred_try_again"))


async def create_promo_code_final(
    callback_or_message: types.Message | types.CallbackQuery,
    state: FSMContext,
    i18n_data: dict,
    settings: Settings,
    session: AsyncSession,
) -> None:
    """Final step - create the promo code in database"""
    current_lang = i18n_data.get("current_language", settings.DEFAULT_LANGUAGE)
    i18n: JsonI18n | None = i18n_data.get("i18n_instance")
    if not i18n:
        return
    _ = lambda key, **kwargs: i18n.gettext(current_lang, key, **kwargs)

    try:
        data = await state.get_data()
        actor = getattr(callback_or_message, "from_user", None)
        created_by_admin_id = int(getattr(actor, "id", 0) or 0)

        # Set validity
        if data.get("validity_days"):
            valid_until = datetime.now(UTC) + timedelta(days=data["validity_days"])
        else:
            valid_until = None

        # Create promo code
        created_promo = await PromoCodeService.issue_code(
            session,
            effects=PromoEffects(
                bonus_days=int(data.get("bonus_days") or 0),
                discount_percent=(
                    float(data["discount_percent"])
                    if data.get("discount_percent") is not None
                    else None
                ),
                applies_to=PROMO_APPLIES_TO_SUBSCRIPTION,
            ),
            code=str(data["promo_code"]),
            max_activations=int(data["max_activations"]),
            valid_until=valid_until,
            origin="admin",
            created_by_admin_id=created_by_admin_id,
            max_duration_multiplier=float(settings.PROMO_DURATION_MULTIPLIER_MAX),
            max_traffic_multiplier=float(settings.PROMO_TRAFFIC_MULTIPLIER_MAX),
        )
        await session.commit()

        # Log successful creation
        logger.info(
            "Promo code '%s' created with ID %s", data["promo_code"], created_promo.promo_code_id
        )

        # Success message
        valid_until_str = (
            _("admin_promo_unlimited")
            if not data.get("validity_days")
            else _("admin_promo_days_value", days=data["validity_days"])
        )
        success_text = _(
            "admin_promo_created_success",
            code=data["promo_code"],
            effect=_promo_effect_label(_, data),
            max_activations=data["max_activations"],
            valid_until_str=valid_until_str,
        )

        if isinstance(callback_or_message, types.CallbackQuery):
            message = callback_message(callback_or_message)
            try:
                await message.edit_text(
                    success_text,
                    reply_markup=get_back_to_admin_panel_keyboard(current_lang, i18n),
                    parse_mode="HTML",
                )
            except Exception:
                await message.answer(
                    success_text,
                    reply_markup=get_back_to_admin_panel_keyboard(current_lang, i18n),
                    parse_mode="HTML",
                )
            await callback_or_message.answer()
        else:  # Message
            await callback_or_message.answer(
                success_text,
                reply_markup=get_back_to_admin_panel_keyboard(current_lang, i18n),
                parse_mode="HTML",
            )

        await state.clear()

    except Exception as e:
        logger.error("Error creating promo code: %s", e)
        error_text = _("error_occurred_try_again")

        if isinstance(callback_or_message, types.CallbackQuery):
            await callback_message(callback_or_message).answer(error_text)
            await callback_or_message.answer()
        else:  # Message
            await callback_or_message.answer(error_text)

        await state.clear()


# Cancel promo creation
@router.callback_query(
    F.data == "admin_action:main",
    StateFilter(
        AdminStates.waiting_for_promo_code,
        AdminStates.waiting_for_promo_type,
        AdminStates.waiting_for_promo_bonus_days,
        AdminStates.waiting_for_promo_discount,
        AdminStates.waiting_for_promo_max_activations,
        AdminStates.waiting_for_promo_validity_days,
    ),
)
async def cancel_promo_creation_state_to_menu(
    callback: types.CallbackQuery,
    state: FSMContext,
    settings: Settings,
    i18n_data: dict,
    session: AsyncSession,
) -> None:
    current_lang = i18n_data.get("current_language", settings.DEFAULT_LANGUAGE)
    i18n: JsonI18n | None = i18n_data.get("i18n_instance")
    if not i18n or not callback.message:
        await callback.answer("Error cancelling.", show_alert=True)
        return
    _ = lambda key, **kwargs: i18n.gettext(current_lang, key, **kwargs)

    try:
        await callback_message(callback).edit_text(
            _(key="admin_panel_title"),
            reply_markup=get_admin_panel_keyboard(i18n, current_lang, settings),
        )
    except Exception:
        await callback_message(callback).answer(
            _(key="admin_panel_title"),
            reply_markup=get_admin_panel_keyboard(i18n, current_lang, settings),
        )

    await callback.answer(_("admin_promo_creation_cancelled"))
    await state.clear()
