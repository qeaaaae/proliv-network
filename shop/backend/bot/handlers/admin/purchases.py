"""Admin purchases section: manual expense tracker with expiry reminders.

The admin registers what was bought from which provider, when it was paid,
and for how long (days/weeks/months/years, entered in free text). A worker
(``purchase_reminder_worker``) pings all ``ADMIN_IDS`` in PM at 10:00 MSK
a few days before ``expires_on``, on the expiry day itself, and once when
a payment goes overdue.
"""

import logging
import re
from calendar import monthrange
from collections.abc import Awaitable, Callable
from datetime import UTC, date, datetime, timedelta, timezone
from html import escape
from typing import Any

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline.admin_keyboards import (
    get_purchase_card_keyboard,
    get_purchase_confirm_keyboard,
    get_purchase_delete_confirm_keyboard,
    get_purchase_step_keyboard,
    get_purchases_menu_keyboard,
)
from bot.middlewares.i18n import JsonI18n
from bot.states.admin_states import AdminStates
from bot.utils.callback_answer import callback_data, callback_message
from config.settings import Settings
from db.admin_purchase_models import AdminPurchase
from db.dal import admin_purchase_dal

logger = logging.getLogger(__name__)

router = Router(name="admin_purchases_router")

PURCHASES_PAGE_SIZE = 8
PURCHASE_PROVIDER_LIMIT = 128
PURCHASE_TITLE_LIMIT = 255
PURCHASE_NOTE_LIMIT = 255
PURCHASE_PRICE_LIMIT = 64
PURCHASE_PERIOD_LIMIT = 64
PURCHASE_PERIOD_MAX_COUNT = 10000

# Admin enters dates and periods in Moscow time (fixed UTC+3, no DST).
PURCHASE_TZ = timezone(timedelta(hours=3))
_PURCHASE_DATE_RE = re.compile(r"^\s*(\d{1,2})\.(\d{1,2})(?:\.(\d{2}|\d{4}))?\s*$")
_PURCHASE_PERIOD_RE = re.compile(r"^\s*(\d+)\s*([a-zA-Zа-яА-ЯёЁ]*)\s*$")
_PURCHASE_TODAY_WORDS = {"сегодня", "today"}
_PRICE_AMOUNT_RE = re.compile(r"(\d[\d\s ]*(?:[.,]\d+)?)")
_FOREIGN_PRICE_RE = re.compile(r"[$€£]")

_PERIOD_UNITS = {
    "": "days",
    "д": "days",
    "дн": "days",
    "день": "days",
    "дня": "days",
    "дней": "days",
    "d": "days",
    "day": "days",
    "days": "days",
    "н": "weeks",
    "нед": "weeks",
    "неделя": "weeks",
    "недели": "weeks",
    "недель": "weeks",
    "неделю": "weeks",
    "w": "weeks",
    "week": "weeks",
    "weeks": "weeks",
    "м": "months",
    "мес": "months",
    "месяц": "months",
    "месяца": "months",
    "месяцы": "months",
    "месяцев": "months",
    "mon": "months",
    "month": "months",
    "months": "months",
    "г": "years",
    "год": "years",
    "года": "years",
    "годы": "years",
    "лет": "years",
    "y": "years",
    "year": "years",
    "years": "years",
}


def _resolve(i18n_data: dict, settings: Settings) -> tuple[str, JsonI18n | None]:
    return i18n_data.get("current_language", settings.DEFAULT_LANGUAGE), i18n_data.get(
        "i18n_instance"
    )


def _today_msk(now: datetime | None = None) -> date:
    ref = now or datetime.now(UTC)
    return ref.astimezone(PURCHASE_TZ).date()


def parse_purchase_date(raw: str, *, now: datetime | None = None) -> date | None:
    """Parse "дд.мм[.гг[гг]]" or "сегодня"/"today" (Moscow date).

    Returns None for malformed input or a future date: the payment day
    cannot be ahead of today.
    """
    text = (raw or "").strip().lower()
    if text in _PURCHASE_TODAY_WORDS:
        return _today_msk(now)
    match = _PURCHASE_DATE_RE.match(raw or "")
    if not match:
        return None
    day, month = int(match.group(1)), int(match.group(2))
    year_raw = match.group(3)
    ref = _today_msk(now)
    if year_raw is None:
        year = ref.year
    else:
        year = int(year_raw)
        if year < 100:
            year += 2000
    try:
        result = date(year, month, day)
    except ValueError:
        return None
    if result > ref:
        return None
    return result


def parse_purchase_period(raw: str) -> tuple[int, str] | None:
    """Parse "30", "45 дней", "2 недели", "6 месяцев", "1 год" into
    (count, unit) where unit is days/weeks/months/years."""
    match = _PURCHASE_PERIOD_RE.match(raw or "")
    if not match:
        return None
    count = int(match.group(1))
    unit = _PERIOD_UNITS.get((match.group(2) or "").lower())
    if unit is None or count < 1 or count > PURCHASE_PERIOD_MAX_COUNT:
        return None
    return count, unit


def _add_months(d: date, months: int) -> date:
    total = d.year * 12 + (d.month - 1) + months
    year, month_index = divmod(total, 12)
    month = month_index + 1
    day = min(d.day, monthrange(year, month)[1])
    return date(year, month, day)


def compute_expiry(paid_on: date, count: int, unit: str) -> date:
    if unit == "days":
        return paid_on + timedelta(days=count)
    if unit == "weeks":
        return paid_on + timedelta(weeks=count)
    if unit == "months":
        return _add_months(paid_on, count)
    if unit == "years":
        return _add_months(paid_on, count * 12)
    raise ValueError(f"unknown period unit: {unit}")


def parse_price_amount(label: str | None) -> float | None:
    """Extract a numeric amount from a free-text price label ("430 ₽/мес" -> 430).

    Labels in foreign currencies ($, €, £) are skipped - they cannot be
    summed into a ruble total."""
    if not label or _FOREIGN_PRICE_RE.search(label):
        return None
    match = _PRICE_AMOUNT_RE.search(label)
    if not match:
        return None
    num = match.group(1).replace(" ", "").replace(" ", "").replace(",", ".")
    try:
        return float(num)
    except ValueError:
        return None


def _format_price_total(total: float) -> str:
    if total == int(total):
        return f"{int(total):,}".replace(",", " ")
    return f"{total:,.2f}".replace(",", " ").rstrip("0").rstrip(".")


def _days_line(_: Callable[..., str], days_left: int) -> str:
    if days_left > 0:
        return _("admin_purchases_days_left", days=days_left)
    if days_left == 0:
        return _("admin_purchases_days_today")
    return _("admin_purchases_days_overdue", days=-days_left)


def _purchase_card_text(_: Callable[..., str], purchase: AdminPurchase, today: date) -> str:
    note_line = (
        _("admin_purchases_card_note", note=escape(str(purchase.note))) if purchase.note else ""
    )
    price_line = (
        _("admin_purchases_card_price", price=escape(str(purchase.price_label)))
        if purchase.price_label
        else ""
    )
    days_left = (purchase.expires_on - today).days
    return _(
        "admin_purchases_card",
        title=escape(str(purchase.title)),
        provider=escape(str(purchase.provider)),
        price=price_line,
        note=note_line,
        paid_on=purchase.paid_on.strftime("%d.%m.%Y"),
        period=escape(str(purchase.period_label)),
        expires_on=purchase.expires_on.strftime("%d.%m.%Y"),
        days=_days_line(_, days_left),
    )


async def _purchases_list_text(
    _: Callable[..., str], session: AsyncSession, page: int
) -> tuple[str, list[AdminPurchase], int, int]:
    total = await admin_purchase_dal.count_purchases(session)
    total_pages = max(1, (total + PURCHASES_PAGE_SIZE - 1) // PURCHASES_PAGE_SIZE)
    page = min(max(page, 0), total_pages - 1)
    purchases = await admin_purchase_dal.list_purchases(
        session, offset=page * PURCHASES_PAGE_SIZE, limit=PURCHASES_PAGE_SIZE
    )
    lines = [_("admin_purchases_menu_title")]
    if not purchases:
        lines.append(_("admin_purchases_menu_empty"))
    else:
        for index, purchase in enumerate(purchases, start=page * PURCHASES_PAGE_SIZE + 1):
            price_part = (
                _("admin_purchases_menu_row_price", price=escape(str(purchase.price_label)))
                if purchase.price_label
                else ""
            )
            lines.append(
                _(
                    "admin_purchases_menu_row",
                    index=index,
                    title=escape(str(purchase.title)),
                    expires=purchase.expires_on.strftime("%d.%m.%Y"),
                    price=price_part,
                )
            )
        rows = await admin_purchase_dal.all_expiry_price_pairs(session)
        if rows:
            nearest = min(expires_on for expires_on, _ in rows)
            total = sum(
                amount
                for expires_on, label in rows
                if expires_on.year == nearest.year
                and expires_on.month == nearest.month
                and (amount := parse_price_amount(label)) is not None
            )
            if total > 0:
                lines.append(
                    _(
                        "admin_purchases_menu_total",
                        month=f"{nearest.month:02d}.{nearest.year}",
                        total=_format_price_total(total),
                    )
                )
    return "\n".join(lines), purchases, total_pages, page


async def _render_purchases_list(
    target_message: types.Message,
    session: AsyncSession,
    _: Callable[..., str],
    page: int,
) -> None:
    text, purchases, total_pages, page = await _purchases_list_text(_, session, page)
    markup = get_purchases_menu_keyboard(_, purchases, page, total_pages)
    try:
        await target_message.edit_text(text, reply_markup=markup, parse_mode="HTML")
    except Exception as e:
        logger.warning("Purchases list edit failed: %s. Sending new.", e)
        await target_message.answer(text, reply_markup=markup, parse_mode="HTML")


async def _render_purchase_card(
    target_message: types.Message,
    purchase: AdminPurchase,
    _: Callable[..., str],
    back_page: int,
) -> None:
    text = _purchase_card_text(_, purchase, _today_msk())
    markup = get_purchase_card_keyboard(_, int(purchase.purchase_id), back_page)
    try:
        await target_message.edit_text(text, reply_markup=markup, parse_mode="HTML")
    except Exception as e:
        logger.warning("Purchase card edit failed: %s. Sending new.", e)
        await target_message.answer(text, reply_markup=markup, parse_mode="HTML")


async def purchases_menu_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    i18n_data: dict,
    settings: Settings,
    session: AsyncSession,
) -> None:
    """Admin panel "Purchases" entry: the list of tracked payments."""
    lang, i18n = _resolve(i18n_data, settings)
    if not i18n or not callback.message:
        await callback.answer("Language service error.", show_alert=True)
        return
    _ = lambda key, **kwargs: i18n.gettext(lang, key, **kwargs)

    await state.clear()
    await _render_purchases_list(callback_message(callback), session, _, 0)
    await callback.answer()


@router.callback_query(F.data.regexp(r"^admin_purchases:page:(\d+)$"))
async def purchases_page_handler(
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
    page = int(callback_data(callback).split(":")[2])
    await _render_purchases_list(callback_message(callback), session, _, page)
    await callback.answer()


@router.callback_query(F.data == "admin_purchases:page_display")
async def purchases_page_display_handler(callback: types.CallbackQuery) -> None:
    await callback.answer()


async def _require_purchase(
    callback: types.CallbackQuery,
    session: AsyncSession,
    _: Callable[..., str],
) -> tuple[AdminPurchase | None, int]:
    parts = callback_data(callback).split(":")
    try:
        purchase_id = int(parts[2])
        back_page = int(parts[3])
    except (IndexError, ValueError):
        await callback.answer(_("admin_purchases_not_found"), show_alert=True)
        return None, 0
    purchase = await admin_purchase_dal.get_purchase(session, purchase_id)
    if purchase is None:
        await callback.answer(_("admin_purchases_not_found"), show_alert=True)
        return None, back_page
    return purchase, back_page


@router.callback_query(F.data.regexp(r"^admin_purchases:card:(\d+):(\d+)$"))
async def purchase_card_handler(
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
    await state.clear()
    purchase, back_page = await _require_purchase(callback, session, _)
    if purchase is None:
        return
    await _render_purchase_card(callback_message(callback), purchase, _, back_page)
    await callback.answer()


@router.callback_query(F.data == "admin_purchases:new")
async def purchase_new_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    i18n_data: dict,
    settings: Settings,
) -> None:
    """Start the composer: ask which provider the payment belongs to."""
    lang, i18n = _resolve(i18n_data, settings)
    if not i18n or not callback.message:
        await callback.answer("Error.", show_alert=True)
        return
    _ = lambda key, **kwargs: i18n.gettext(lang, key, **kwargs)

    prompt_text = _("admin_purchases_enter_provider")
    prompt_markup = get_purchase_step_keyboard(_, skip_callback=None)
    try:
        await callback_message(callback).edit_text(prompt_text, reply_markup=prompt_markup)
    except Exception as e:
        logger.warning("Could not edit message for purchase prompt: %s. Sending new.", e)
        await callback_message(callback).answer(prompt_text, reply_markup=prompt_markup)
    await callback.answer()
    await state.clear()
    await state.set_state(AdminStates.waiting_for_purchase_provider)


async def _ask_purchase_title(
    answer: Callable[..., Awaitable[Any]], state: FSMContext, _: Callable[..., str]
) -> None:
    await answer(
        _("admin_purchases_enter_title"),
        reply_markup=get_purchase_step_keyboard(_, skip_callback=None),
    )
    await state.set_state(AdminStates.waiting_for_purchase_title)


async def _ask_purchase_price(
    answer: Callable[..., Awaitable[Any]], state: FSMContext, _: Callable[..., str]
) -> None:
    await answer(
        _("admin_purchases_enter_price"),
        reply_markup=get_purchase_step_keyboard(_, skip_callback="admin_purchases:skip_price"),
    )
    await state.set_state(AdminStates.waiting_for_purchase_price)


async def _ask_purchase_note(
    answer: Callable[..., Awaitable[Any]], state: FSMContext, _: Callable[..., str]
) -> None:
    await answer(
        _("admin_purchases_enter_note"),
        reply_markup=get_purchase_step_keyboard(_, skip_callback="admin_purchases:skip_note"),
    )
    await state.set_state(AdminStates.waiting_for_purchase_note)


async def _ask_purchase_paid_on(
    answer: Callable[..., Awaitable[Any]], state: FSMContext, _: Callable[..., str]
) -> None:
    await answer(
        _("admin_purchases_enter_paid_on"),
        reply_markup=get_purchase_step_keyboard(_, skip_callback=None),
    )
    await state.set_state(AdminStates.waiting_for_purchase_paid_on)


async def _ask_purchase_period(
    answer: Callable[..., Awaitable[Any]], state: FSMContext, _: Callable[..., str]
) -> None:
    await answer(
        _("admin_purchases_enter_period"),
        reply_markup=get_purchase_step_keyboard(_, skip_callback=None),
    )
    await state.set_state(AdminStates.waiting_for_purchase_period)


@router.message(AdminStates.waiting_for_purchase_provider)
async def process_purchase_provider_handler(
    message: types.Message,
    state: FSMContext,
    i18n_data: dict,
    settings: Settings,
) -> None:
    lang, i18n = _resolve(i18n_data, settings)
    _ = lambda key, **kwargs: i18n.gettext(lang, key, **kwargs) if i18n else key
    provider = (message.text or "").strip()
    if not provider or len(provider) > PURCHASE_PROVIDER_LIMIT:
        await message.answer(
            _("admin_purchases_too_long", max=PURCHASE_PROVIDER_LIMIT)
            if provider
            else _("admin_purchases_enter_provider"),
            reply_markup=get_purchase_step_keyboard(_, skip_callback=None),
        )
        return
    await state.update_data(purchase_provider=provider)
    await _ask_purchase_title(message.answer, state, _)


@router.message(AdminStates.waiting_for_purchase_title)
async def process_purchase_title_handler(
    message: types.Message,
    state: FSMContext,
    i18n_data: dict,
    settings: Settings,
) -> None:
    lang, i18n = _resolve(i18n_data, settings)
    _ = lambda key, **kwargs: i18n.gettext(lang, key, **kwargs) if i18n else key
    title = (message.text or "").strip()
    if not title or len(title) > PURCHASE_TITLE_LIMIT:
        await message.answer(
            _("admin_purchases_too_long", max=PURCHASE_TITLE_LIMIT)
            if title
            else _("admin_purchases_enter_title"),
            reply_markup=get_purchase_step_keyboard(_, skip_callback=None),
        )
        return
    await state.update_data(purchase_title=title)
    await _ask_purchase_price(message.answer, state, _)


@router.message(AdminStates.waiting_for_purchase_price)
async def process_purchase_price_handler(
    message: types.Message,
    state: FSMContext,
    i18n_data: dict,
    settings: Settings,
) -> None:
    lang, i18n = _resolve(i18n_data, settings)
    _ = lambda key, **kwargs: i18n.gettext(lang, key, **kwargs) if i18n else key
    price = (message.text or "").strip()
    if not price:
        await message.answer(
            _("admin_purchases_enter_price"),
            reply_markup=get_purchase_step_keyboard(_, skip_callback="admin_purchases:skip_price"),
        )
        return
    if len(price) > PURCHASE_PRICE_LIMIT:
        await message.answer(
            _("admin_purchases_too_long", max=PURCHASE_PRICE_LIMIT),
            reply_markup=get_purchase_step_keyboard(_, skip_callback="admin_purchases:skip_price"),
        )
        return
    await state.update_data(purchase_price_label=price)
    await _ask_purchase_note(message.answer, state, _)


@router.callback_query(
    F.data == "admin_purchases:skip_price", AdminStates.waiting_for_purchase_price
)
async def skip_purchase_price_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    i18n_data: dict,
    settings: Settings,
) -> None:
    lang, i18n = _resolve(i18n_data, settings)
    _ = lambda key, **kwargs: i18n.gettext(lang, key, **kwargs) if i18n else key
    await state.update_data(purchase_price_label=None)
    await _ask_purchase_note(callback_message(callback).answer, state, _)
    await callback.answer()


@router.message(AdminStates.waiting_for_purchase_note)
async def process_purchase_note_handler(
    message: types.Message,
    state: FSMContext,
    i18n_data: dict,
    settings: Settings,
) -> None:
    lang, i18n = _resolve(i18n_data, settings)
    _ = lambda key, **kwargs: i18n.gettext(lang, key, **kwargs) if i18n else key
    note = (message.text or "").strip()
    if not note:
        await message.answer(
            _("admin_purchases_enter_note"),
            reply_markup=get_purchase_step_keyboard(_, skip_callback="admin_purchases:skip_note"),
        )
        return
    if len(note) > PURCHASE_NOTE_LIMIT:
        await message.answer(
            _("admin_purchases_too_long", max=PURCHASE_NOTE_LIMIT),
            reply_markup=get_purchase_step_keyboard(_, skip_callback="admin_purchases:skip_note"),
        )
        return
    await state.update_data(purchase_note=note)
    await _ask_purchase_paid_on(message.answer, state, _)


@router.callback_query(F.data == "admin_purchases:skip_note", AdminStates.waiting_for_purchase_note)
async def skip_purchase_note_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    i18n_data: dict,
    settings: Settings,
) -> None:
    lang, i18n = _resolve(i18n_data, settings)
    _ = lambda key, **kwargs: i18n.gettext(lang, key, **kwargs) if i18n else key
    await state.update_data(purchase_note=None)
    await _ask_purchase_paid_on(callback_message(callback).answer, state, _)
    await callback.answer()


@router.message(AdminStates.waiting_for_purchase_paid_on)
async def process_purchase_paid_on_handler(
    message: types.Message,
    state: FSMContext,
    i18n_data: dict,
    settings: Settings,
) -> None:
    lang, i18n = _resolve(i18n_data, settings)
    _ = lambda key, **kwargs: i18n.gettext(lang, key, **kwargs) if i18n else key
    when = parse_purchase_date(message.text or "")
    if when is None:
        await message.answer(
            _("admin_purchases_invalid_date"),
            reply_markup=get_purchase_step_keyboard(_, skip_callback=None),
        )
        return
    await state.update_data(purchase_paid_on=when.isoformat())
    await _ask_purchase_period(message.answer, state, _)


async def _finish_purchase_period(
    message: types.Message,
    state: FSMContext,
    _: Callable[..., str],
) -> None:
    raw = (message.text or "").strip()
    parsed = parse_purchase_period(raw)
    if parsed is None or len(raw) > PURCHASE_PERIOD_LIMIT:
        await message.answer(
            _("admin_purchases_invalid_period"),
            reply_markup=get_purchase_step_keyboard(_, skip_callback=None),
        )
        return
    count, unit = parsed
    data = await state.get_data()
    paid_on = date.fromisoformat(str(data["purchase_paid_on"]))
    expires_on = compute_expiry(paid_on, count, unit)
    preview = AdminPurchase(
        provider=str(data.get("purchase_provider") or ""),
        title=str(data.get("purchase_title") or ""),
        note=data.get("purchase_note"),
        price_label=data.get("purchase_price_label"),
        paid_on=paid_on,
        period_label=raw,
        expires_on=expires_on,
    )
    await state.update_data(purchase_period_label=raw)
    await message.answer(
        _("admin_purchases_confirm_prompt", card=_purchase_card_text(_, preview, _today_msk())),
        reply_markup=get_purchase_confirm_keyboard(_),
        parse_mode="HTML",
    )
    await state.set_state(AdminStates.confirming_purchase)


@router.message(AdminStates.waiting_for_purchase_period)
async def process_purchase_period_handler(
    message: types.Message,
    state: FSMContext,
    i18n_data: dict,
    settings: Settings,
) -> None:
    lang, i18n = _resolve(i18n_data, settings)
    _ = lambda key, **kwargs: i18n.gettext(lang, key, **kwargs) if i18n else key
    await _finish_purchase_period(message, state, _)


@router.callback_query(F.data == "admin_purchases:save", AdminStates.confirming_purchase)
async def purchase_save_handler(
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
    paid_on = date.fromisoformat(str(data["purchase_paid_on"]))
    parsed = parse_purchase_period(str(data.get("purchase_period_label") or ""))
    if parsed is None:
        await callback.answer(_("admin_purchases_invalid_period"), show_alert=True)
        await state.clear()
        return
    count, unit = parsed
    purchase = await admin_purchase_dal.create_purchase(
        session,
        provider=str(data.get("purchase_provider") or ""),
        title=str(data.get("purchase_title") or ""),
        note=data.get("purchase_note"),
        price_label=data.get("purchase_price_label"),
        paid_on=paid_on,
        period_label=str(data.get("purchase_period_label") or ""),
        expires_on=compute_expiry(paid_on, count, unit),
        created_by_telegram_id=callback.from_user.id,
    )
    try:
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.exception("Purchase create commit failed: %s", e)
        await callback.answer(_("error_occurred_try_again"), show_alert=True)
        return
    await state.clear()
    await callback.answer(_("admin_purchases_saved"))
    await _render_purchases_list(callback_message(callback), session, _, 0)
    logger.info("Admin purchase %s created by %s", purchase.purchase_id, callback.from_user.id)


@router.callback_query(F.data == "admin_purchases:save")
async def purchase_save_stale_handler(callback: types.CallbackQuery) -> None:
    await callback.answer("Purchase draft expired.", show_alert=True)


@router.callback_query(F.data.regexp(r"^admin_purchases:renew:(\d+):(\d+)$"))
async def purchase_renew_prompt_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    i18n_data: dict,
    settings: Settings,
    session: AsyncSession,
) -> None:
    """Card "renew" button: ask for the new payment date, then the period."""
    lang, i18n = _resolve(i18n_data, settings)
    if not i18n or not callback.message:
        await callback.answer("Error.", show_alert=True)
        return
    _ = lambda key, **kwargs: i18n.gettext(lang, key, **kwargs)
    purchase, back_page = await _require_purchase(callback, session, _)
    if purchase is None:
        return
    await state.clear()
    await state.update_data(renew_purchase_id=int(purchase.purchase_id), renew_back_page=back_page)
    prompt_text = _("admin_purchases_enter_paid_on")
    prompt_markup = get_purchase_step_keyboard(_, skip_callback=None)
    try:
        await callback_message(callback).edit_text(prompt_text, reply_markup=prompt_markup)
    except Exception:
        await callback_message(callback).answer(prompt_text, reply_markup=prompt_markup)
    await state.set_state(AdminStates.waiting_for_purchase_renew_paid_on)
    await callback.answer()


@router.message(AdminStates.waiting_for_purchase_renew_paid_on)
async def process_purchase_renew_paid_on_handler(
    message: types.Message,
    state: FSMContext,
    i18n_data: dict,
    settings: Settings,
) -> None:
    lang, i18n = _resolve(i18n_data, settings)
    _ = lambda key, **kwargs: i18n.gettext(lang, key, **kwargs) if i18n else key
    when = parse_purchase_date(message.text or "")
    if when is None:
        await message.answer(
            _("admin_purchases_invalid_date"),
            reply_markup=get_purchase_step_keyboard(_, skip_callback=None),
        )
        return
    await state.update_data(purchase_paid_on=when.isoformat())
    await message.answer(
        _("admin_purchases_renew_enter_price"),
        reply_markup=get_purchase_step_keyboard(
            _, skip_callback="admin_purchases:skip_renew_price"
        ),
    )
    await state.set_state(AdminStates.waiting_for_purchase_renew_price)


@router.message(AdminStates.waiting_for_purchase_renew_price)
async def process_purchase_renew_price_handler(
    message: types.Message,
    state: FSMContext,
    i18n_data: dict,
    settings: Settings,
) -> None:
    lang, i18n = _resolve(i18n_data, settings)
    _ = lambda key, **kwargs: i18n.gettext(lang, key, **kwargs) if i18n else key
    price = (message.text or "").strip()
    if not price or len(price) > PURCHASE_PRICE_LIMIT:
        await message.answer(
            _("admin_purchases_renew_enter_price")
            if not price
            else _("admin_purchases_too_long", max=PURCHASE_PRICE_LIMIT),
            reply_markup=get_purchase_step_keyboard(
                _, skip_callback="admin_purchases:skip_renew_price"
            ),
        )
        return
    await state.update_data(renew_price_label=price)
    await message.answer(
        _("admin_purchases_enter_period"),
        reply_markup=get_purchase_step_keyboard(_, skip_callback=None),
    )
    await state.set_state(AdminStates.waiting_for_purchase_renew_period)


@router.callback_query(
    F.data == "admin_purchases:skip_renew_price",
    AdminStates.waiting_for_purchase_renew_price,
)
async def skip_purchase_renew_price_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    i18n_data: dict,
    settings: Settings,
) -> None:
    lang, i18n = _resolve(i18n_data, settings)
    _ = lambda key, **kwargs: i18n.gettext(lang, key, **kwargs) if i18n else key
    await state.update_data(renew_price_label=None)
    await callback_message(callback).answer(
        _("admin_purchases_enter_period"),
        reply_markup=get_purchase_step_keyboard(_, skip_callback=None),
    )
    await state.set_state(AdminStates.waiting_for_purchase_renew_period)
    await callback.answer()


@router.message(AdminStates.waiting_for_purchase_renew_period)
async def process_purchase_renew_period_handler(
    message: types.Message,
    state: FSMContext,
    i18n_data: dict,
    settings: Settings,
    session: AsyncSession,
) -> None:
    lang, i18n = _resolve(i18n_data, settings)
    _ = lambda key, **kwargs: i18n.gettext(lang, key, **kwargs) if i18n else key
    raw = (message.text or "").strip()
    parsed = parse_purchase_period(raw)
    if parsed is None or len(raw) > PURCHASE_PERIOD_LIMIT:
        await message.answer(
            _("admin_purchases_invalid_period"),
            reply_markup=get_purchase_step_keyboard(_, skip_callback=None),
        )
        return
    count, unit = parsed
    data = await state.get_data()
    purchase_id = data.get("renew_purchase_id")
    back_page = int(data.get("renew_back_page") or 0)
    purchase = (
        await admin_purchase_dal.get_purchase(session, int(purchase_id))
        if purchase_id is not None
        else None
    )
    if purchase is None:
        await message.answer(_("admin_purchases_not_found"))
        await state.clear()
        return
    paid_on = date.fromisoformat(str(data["purchase_paid_on"]))
    await admin_purchase_dal.renew_purchase(
        session,
        purchase,
        paid_on=paid_on,
        period_label=raw,
        expires_on=compute_expiry(paid_on, count, unit),
        price_label=data.get("renew_price_label"),
    )
    try:
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.exception("Purchase %s renew commit failed: %s", purchase.purchase_id, e)
        await message.answer(_("error_occurred_try_again"))
        await state.clear()
        return
    await state.clear()
    await message.answer(_("admin_purchases_renewed"))
    await message.answer(
        _purchase_card_text(_, purchase, _today_msk()),
        reply_markup=get_purchase_card_keyboard(_, int(purchase.purchase_id), back_page),
        parse_mode="HTML",
    )


@router.callback_query(F.data.regexp(r"^admin_purchases:delete:(\d+):(\d+)$"))
async def purchase_delete_prompt_handler(
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
    purchase, back_page = await _require_purchase(callback, session, _)
    if purchase is None:
        return
    text = _(
        "admin_purchases_delete_confirm_text",
        purchase_id=int(purchase.purchase_id),
        title=escape(str(purchase.title)),
    )
    markup = get_purchase_delete_confirm_keyboard(_, int(purchase.purchase_id), back_page)
    try:
        await callback_message(callback).edit_text(text, reply_markup=markup, parse_mode="HTML")
    except Exception:
        await callback_message(callback).answer(text, reply_markup=markup, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.regexp(r"^admin_purchases:delete_confirm:(\d+):(\d+)$"))
async def purchase_delete_handler(
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
    purchase, back_page = await _require_purchase(callback, session, _)
    if purchase is None:
        return
    await admin_purchase_dal.delete_purchase(session, purchase)
    try:
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.exception("Purchase delete commit failed: %s", e)
        await callback.answer(_("error_occurred_try_again"), show_alert=True)
        return
    await callback.answer(_("admin_purchases_deleted"))
    await _render_purchases_list(callback_message(callback), session, _, back_page)


@router.callback_query(F.data == "admin_purchases:cancel")
async def cancel_purchase_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    i18n_data: dict,
    settings: Settings,
    session: AsyncSession,
) -> None:
    """Composer cancel: drop the flow and return to the purchases list."""
    lang, i18n = _resolve(i18n_data, settings)
    if not i18n or not callback.message:
        await callback.answer("Error cancelling.", show_alert=True)
        return
    _ = lambda key, **kwargs: i18n.gettext(lang, key, **kwargs)
    await state.clear()
    await _render_purchases_list(callback_message(callback), session, _, 0)
    await callback.answer()
