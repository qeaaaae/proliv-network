"""Admin support-ticket flow inside the bot chat.

Ticket notifications used to push admins into the web panel for every step.
The whole loop вЂ” read the thread, answer, change status вЂ” fits one bot
message: ``admin_ticket:<id>`` renders the ticket, ``admin_ticket_reply:<id>``
starts an FSM reply, and ``admin_ticket_status:<id>:<status>`` transitions the
ticket. The log channel cannot deliver callbacks, so its buttons deep-link to
``/start admin_ticket_<id>``, which lands on the same view.
"""

import logging
from collections.abc import Awaitable, Callable

from aiogram import Bot, F, Router, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.utils.text_decorations import html_decoration as hd
from sqlalchemy.ext.asyncio import AsyncSession

from bot.middlewares.i18n import JsonI18n
from bot.services.broadcast_personalization import telegram_html_error
from bot.services.support_message_body import (
    BODY_FORMAT_HTML,
    support_body_telegram_html,
)
from bot.services.support_service import SupportService
from bot.services.telegram_account import (
    TelegramAccountRequiredError,
    require_telegram_account_id,
)
from bot.states.admin_states import AdminStates
from bot.utils.callback_answer import callback_data, callback_message
from config.settings import Settings
from db.dal import support_dal, user_dal
from db.models import SupportTicket, SupportTicketMessage

logger = logging.getLogger(__name__)

router = Router(name="admin_support_router")

_TICKET_MESSAGE_LIMIT = 6
_TICKET_MESSAGE_BODY_LIMIT = 400
_TICKET_STATUS_EMOJI = {
    "open": "рџџў",
    "awaiting_user": "вЏі",
    "awaiting_admin": "🟠",
    "resolved": "вњ…",
    "closed": "рџ”’",
}
_TICKET_STATUS_VALUES = set(_TICKET_STATUS_EMOJI)


def _ticket_translate(i18n: JsonI18n | None, lang: str) -> Callable[..., str]:
    return lambda key, **kwargs: i18n.gettext(lang, key, **kwargs) if i18n else key


def _format_ticket_author(
    message: SupportTicketMessage,
    _: Callable[..., str],
) -> str:
    if message.is_internal_note:
        return _("admin_ticket_author_internal_note")
    if message.author_role == "user":
        return _("admin_ticket_author_user")
    if message.author_role == "connector" and message.author_label:
        return hd.quote(str(message.author_label))
    return _("admin_ticket_author_admin")


def _format_ticket_message(
    message: SupportTicketMessage,
    _: Callable[..., str],
) -> str:
    created = message.created_at.strftime("%d.%m.%Y %H:%M") if message.created_at else "вЂ”"
    body_html = support_body_telegram_html(
        message.body or "",
        str(getattr(message, "body_format", "text") or "text"),
        limit=_TICKET_MESSAGE_BODY_LIMIT,
    )
    image_marker = " рџ“Ћ" if getattr(message, "image_id", None) else ""
    return f"<b>{_format_ticket_author(message, _)}</b> В· {created}{image_marker}\n{body_html}"


def _ticket_keyboard(
    ticket: SupportTicket,
    user_id: int,
    _: Callable[..., str],
) -> types.InlineKeyboardMarkup:
    ticket_id = int(ticket.ticket_id)
    rows: list[list[types.InlineKeyboardButton]] = [
        [
            types.InlineKeyboardButton(
                text=_("admin_ticket_reply_button"),
                callback_data=f"admin_ticket_reply:{ticket_id}",
            )
        ]
    ]
    if ticket.status in support_dal.CLOSED_STATUSES:
        status_row = [
            types.InlineKeyboardButton(
                text=_("admin_ticket_reopen_button"),
                callback_data=f"admin_ticket_status:{ticket_id}:open",
            )
        ]
    else:
        status_row = [
            types.InlineKeyboardButton(
                text=_("admin_ticket_resolve_button"),
                callback_data=f"admin_ticket_status:{ticket_id}:resolved",
            ),
            types.InlineKeyboardButton(
                text=_("admin_ticket_close_button"),
                callback_data=f"admin_ticket_status:{ticket_id}:closed",
            ),
        ]
    rows.append(status_row)
    rows.append(
        [
            types.InlineKeyboardButton(
                text=_("support_user_card_button"),
                callback_data=f"admin_user_card_from_list:{user_id}:0",
            ),
            types.InlineKeyboardButton(
                text=_("admin_ticket_refresh_button"),
                callback_data=f"admin_ticket:{ticket_id}",
            ),
        ]
    )
    return types.InlineKeyboardMarkup(inline_keyboard=rows)


async def build_admin_ticket_view(
    session: AsyncSession,
    ticket_id: int,
    _: Callable[..., str],
) -> tuple[str, types.InlineKeyboardMarkup] | None:
    ticket, messages = await support_dal.get_ticket(
        session,
        ticket_id,
        include_internal=True,
        limit=_TICKET_MESSAGE_LIMIT,
    )
    if ticket is None:
        return None
    user = await user_dal.get_user_by_id(session, ticket.user_id)
    user_name = (
        " ".join(
            part
            for part in [getattr(user, "first_name", None), getattr(user, "last_name", None)]
            if part
        )
        or "вЂ”"
    )
    if user and getattr(user, "username", None):
        user_name = f"{user_name} @{user.username}"
    user_id_display = getattr(user, "minishop_id", None) or "вЂ”"
    status = str(ticket.status or "open")
    status_label = _(
        f"admin_ticket_status_{status}"
        if status in _TICKET_STATUS_VALUES
        else "admin_ticket_status_open"
    )
    parts: list[str] = [
        _(
            "admin_ticket_header",
            ticket_id=ticket_id,
            status_emoji=_TICKET_STATUS_EMOJI.get(status, "вќ”"),
            status=hd.quote(status_label),
            subject=hd.quote(str(ticket.subject or "вЂ”")),
            priority=hd.quote(str(ticket.priority or "вЂ”")),
            category=hd.quote(str(ticket.category or "вЂ”")),
        ),
        _(
            "admin_ticket_user_line",
            user=hd.quote(user_name),
            user_id=hd.quote(str(user_id_display)),
        ),
    ]
    if not messages:
        parts.append(_("admin_ticket_messages_empty"))
    else:
        parts.append("вЂ”" * 12)
        parts.extend(_format_ticket_message(message, _) for message in messages)
    text = "\n\n".join(parts)
    # Drop the oldest rendered messages until the caption fits Telegram.
    while len(text) > 4000 and len(messages) > 1:
        messages = messages[1:]
        parts = parts[:3] + [_format_ticket_message(message, _) for message in messages]
        text = "\n\n".join(parts)
    if len(text) > 4000:
        text = text[:3999] + "вЂ¦"
    return text, _ticket_keyboard(ticket, int(ticket.user_id), _)


async def _render_ticket_into(
    target: Callable[..., Awaitable[object]],
    session: AsyncSession,
    ticket_id: int,
    _: Callable[..., str],
) -> bool:
    rendered = await build_admin_ticket_view(session, ticket_id, _)
    if rendered is None:
        return False
    text, markup = rendered
    try:
        await target(text=text, reply_markup=markup, parse_mode="HTML")
    except TelegramBadRequest as error:
        if "message is not modified" in str(error).lower():
            return True
        raise
    return True


def _translator(i18n_data: dict, default_lang: str) -> Callable[..., str]:
    return _ticket_translate(
        i18n_data.get("i18n_instance"),
        i18n_data.get("current_language", default_lang),
    )


@router.callback_query(F.data.regexp(r"^admin_ticket:\d+$"))
async def admin_ticket_view_handler(
    callback: types.CallbackQuery,
    i18n_data: dict,
    settings: Settings,
    support_service: SupportService,
    session: AsyncSession,
) -> None:
    _ = _translator(i18n_data, settings.DEFAULT_LANGUAGE)
    if not callback.message:
        await callback.answer(_("error_occurred_try_again"), show_alert=True)
        return
    ticket_id = int(callback_data(callback).rsplit(":", 1)[1])
    try:
        opened = await _render_ticket_into(
            callback_message(callback).edit_text,
            session,
            ticket_id,
            _,
        )
    except Exception:
        logger.exception("Failed to render ticket %s for admin.", ticket_id)
        opened = False
    if not opened:
        await callback.answer(_("admin_ticket_not_found"), show_alert=True)
        return
    try:
        await support_service.mark_read_as_admin(ticket_id)
    except Exception:
        logger.warning("Failed to mark ticket %s read for admin.", ticket_id)
    await callback.answer()


@router.callback_query(F.data.regexp(r"^admin_ticket_status:\d+:(open|resolved|closed)$"))
async def admin_ticket_status_handler(
    callback: types.CallbackQuery,
    i18n_data: dict,
    settings: Settings,
    support_service: SupportService,
    session: AsyncSession,
) -> None:
    _ = _translator(i18n_data, settings.DEFAULT_LANGUAGE)
    if not callback.message:
        await callback.answer(_("error_occurred_try_again"), show_alert=True)
        return
    parts = callback_data(callback).split(":")
    ticket_id, new_status = int(parts[1]), parts[2]
    try:
        admin_id = await require_telegram_account_id(session, callback.from_user.id)
        if new_status == "closed":
            await support_service.close_ticket(admin_id, ticket_id)
        else:
            await support_service.change_status(admin_id, ticket_id, new_status)
    except TelegramAccountRequiredError:
        await callback.answer(_("admin_ticket_open_error"), show_alert=True)
        return
    except Exception:
        logger.exception("Failed to set ticket %s status to %s.", ticket_id, new_status)
        await callback.answer(_("admin_ticket_status_failed"), show_alert=True)
        return
    try:
        await _render_ticket_into(
            callback_message(callback).edit_text,
            session,
            ticket_id,
            _,
        )
    except Exception:
        logger.exception("Failed to refresh ticket %s view.", ticket_id)
    await callback.answer(_("admin_ticket_status_updated"))


@router.callback_query(F.data.regexp(r"^admin_ticket_reply:\d+$"))
async def admin_ticket_reply_prompt_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    i18n_data: dict,
    settings: Settings,
) -> None:
    _ = _translator(i18n_data, settings.DEFAULT_LANGUAGE)
    if not callback.message:
        await callback.answer(_("error_occurred_try_again"), show_alert=True)
        return
    ticket_id = int(callback_data(callback).rsplit(":", 1)[1])
    prompt_markup = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text=_("cancel_button"),
                    callback_data=f"admin_ticket:{ticket_id}",
                )
            ]
        ]
    )
    try:
        await callback_message(callback).edit_text(
            _("admin_ticket_reply_prompt", ticket_id=ticket_id),
            reply_markup=prompt_markup,
            parse_mode="HTML",
        )
    except Exception:
        await callback_message(callback).answer(
            _("admin_ticket_reply_prompt", ticket_id=ticket_id),
            reply_markup=prompt_markup,
        )
    await state.update_data(
        support_ticket_id=ticket_id,
        support_prompt_message_id=callback_message(callback).message_id,
    )
    await state.set_state(AdminStates.waiting_for_support_reply)
    await callback.answer()


@router.message(AdminStates.waiting_for_support_reply)
async def admin_ticket_reply_message_handler(
    message: types.Message,
    state: FSMContext,
    i18n_data: dict,
    settings: Settings,
    support_service: SupportService,
    bot: Bot,
    session: AsyncSession,
) -> None:
    _ = _translator(i18n_data, settings.DEFAULT_LANGUAGE)
    data = await state.get_data()
    ticket_id = int(data.get("support_ticket_id") or 0)
    prompt_message_id = int(data.get("support_prompt_message_id") or 0)
    if not ticket_id:
        await state.clear()
        await message.answer(_("admin_ticket_not_found"))
        return

    body = (message.html_text or "").strip()
    if not body:
        await message.answer(_("admin_ticket_reply_empty"))
        return
    html_error = telegram_html_error(body)
    if html_error:
        await message.answer(_("admin_broadcast_invalid_telegram_html", error=html_error))
        return

    try:
        admin_id = await require_telegram_account_id(
            session, int(getattr(message.from_user, "id", 0) or 0)
        )
        await support_service.reply_as_admin(
            admin_id,
            ticket_id,
            body,
            body_format=BODY_FORMAT_HTML,
        )
    except TelegramAccountRequiredError:
        await state.clear()
        await message.answer(_("admin_ticket_open_error"))
        return
    except Exception:
        logger.exception("Failed to send admin reply for ticket %s.", ticket_id)
        await message.answer(_("admin_ticket_reply_failed"))
        return
    await state.clear()

    rendered = await build_admin_ticket_view(session, ticket_id, _)
    if rendered is None:
        await message.answer(_("admin_ticket_reply_sent"))
        return
    text, markup = rendered
    if prompt_message_id:
        try:
            await bot.edit_message_text(
                text=text,
                chat_id=message.chat.id,
                message_id=prompt_message_id,
                reply_markup=markup,
                parse_mode="HTML",
            )
            return
        except Exception:
            logger.warning("Failed to refresh ticket %s view after reply.", ticket_id)
    await message.answer(text, reply_markup=markup, parse_mode="HTML")
