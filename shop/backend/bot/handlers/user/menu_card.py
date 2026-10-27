"""Photo-card navigation: one bot message whose caption+keyboard change per state.

The card image ships out-of-band in the shared shop-data volume
(`/app/data/branding/welcome.png`). When the file is absent every helper
degrades to the legacy plain-text edit/answer behavior, so the bot stays
functional without branding assets.

Telegram constraints handled here:
- captions are limited to ~1024 chars, so longer texts render as text;
- `edit_text` does not work on media messages and `edit_caption` does not
  work on text messages, so a type mismatch means delete + resend;
- the uploaded file_id is cached so subsequent sends are cheap.
"""

import contextlib
import logging
from pathlib import Path

from aiogram import Bot, types
from aiogram.types import FSInputFile

logger = logging.getLogger(__name__)

CARD_PHOTO_PATH = Path("/app/data/branding/welcome.png")
MAX_CAPTION_LEN = 1000

_card_file_id: str | None = None


def _parse_kwargs(parse_mode: str | None) -> dict[str, str]:
    # Explicit parse_mode=None disables the bot default (HTML); omit the kwarg instead.
    return {"parse_mode": parse_mode} if parse_mode is not None else {}


def card_enabled() -> bool:
    return CARD_PHOTO_PATH.is_file()


def _photo_source() -> str | FSInputFile:
    return _card_file_id or FSInputFile(CARD_PHOTO_PATH)


def _cache_file_id(sent: types.Message) -> None:
    global _card_file_id
    if sent.photo:
        _card_file_id = sent.photo[-1].file_id


async def send_card(
    bot: Bot,
    chat_id: int,
    text: str,
    reply_markup: types.InlineKeyboardMarkup | None = None,
    *,
    disable_web_page_preview: bool = True,
    parse_mode: str | None = None,
) -> types.Message:
    """Always send a new card (used for commands and fresh screens)."""
    if card_enabled() and len(text) <= MAX_CAPTION_LEN:
        try:
            sent = await bot.send_photo(
                chat_id,
                photo=_photo_source(),
                caption=text,
                reply_markup=reply_markup,
                **_parse_kwargs(parse_mode),
            )
            _cache_file_id(sent)
            return sent
        except Exception:
            logger.exception("Photo card send failed, falling back to text")
    return await bot.send_message(
        chat_id,
        text,
        reply_markup=reply_markup,
        disable_web_page_preview=disable_web_page_preview,
        **_parse_kwargs(parse_mode),
    )


async def render_card(
    target: types.Message | types.CallbackQuery,
    text: str,
    reply_markup: types.InlineKeyboardMarkup | None = None,
    *,
    disable_web_page_preview: bool = True,
    parse_mode: str | None = None,
    is_edit: bool = True,
) -> None:
    """Render a navigation state in place: caption edit when possible.

    `is_edit=False` on a callback forces delete + resend (matching the
    legacy `answer` semantic for "keep old message" actions).
    """
    if isinstance(target, types.CallbackQuery):
        message = target.message
        bot = target.bot
        if message is None or bot is None:
            return
    else:
        message = target
        bot = message.bot
        if bot is None:
            return
        is_edit = False  # user-triggered commands always produce a new card

    fits_caption = len(text) <= MAX_CAPTION_LEN

    if not card_enabled():
        if is_edit:
            try:
                await message.edit_text(
                    text,
                    reply_markup=reply_markup,
                    disable_web_page_preview=disable_web_page_preview,
                    **_parse_kwargs(parse_mode),
                )
                return
            except Exception:
                pass
        await bot.send_message(
            message.chat.id,
            text,
            reply_markup=reply_markup,
            disable_web_page_preview=disable_web_page_preview,
            **_parse_kwargs(parse_mode),
        )
        return

    if is_edit and message.photo and fits_caption:
        try:
            await message.edit_caption(
                caption=text, reply_markup=reply_markup, **_parse_kwargs(parse_mode)
            )
            return
        except Exception:
            logger.warning("edit_caption failed, replacing card message", exc_info=True)

    with contextlib.suppress(Exception):
        await message.delete()

    if fits_caption:
        try:
            sent = await bot.send_photo(
                message.chat.id,
                photo=_photo_source(),
                caption=text,
                reply_markup=reply_markup,
                **_parse_kwargs(parse_mode),
            )
            _cache_file_id(sent)
            return
        except Exception:
            logger.exception("Photo card resend failed, falling back to text")
    await bot.send_message(
        message.chat.id,
        text,
        reply_markup=reply_markup,
        disable_web_page_preview=disable_web_page_preview,
        **_parse_kwargs(parse_mode),
    )
