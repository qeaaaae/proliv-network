"""Bounded custom emoji fallback for immediate and queued Telegram delivery."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import time
from collections.abc import Set
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal

from aiogram import Bot
from aiogram.client.default import Default
from aiogram.client.session.base import TelegramType
from aiogram.client.session.middlewares.base import BaseRequestMiddleware, NextRequestMiddlewareType
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import Response, TelegramMethod
from aiogram.types import InlineKeyboardMarkup, Message

from bot.services.telegram_emoji_catalog import load_set, resolve_ids
from bot.services.telegram_emoji_storage import capabilities, observe_capability, read_item
from bot.utils.custom_emoji import (
    custom_emoji_unicode_html,
    split_decorative_emoji,
    unicode_emoji_to_custom_html,
)
from config.telegram_menu import parse_emoji_library

if TYPE_CHECKING:
    from config.settings import Settings

logger = logging.getLogger(__name__)

CUSTOM_EMOJI_PROBE: ContextVar[bool] = ContextVar("telegram_custom_emoji_probe", default=False)
_PERMISSION_ERRORS = (
    "premium account required",
    "premium_account_required",
    "custom emoji are not allowed",
    "custom emoji is not allowed",
    "custom_emoji_not_allowed",
    "custom emoji usage is not allowed",
    "bot can't use custom emoji",
    "bot cannot use custom emoji",
)
_INVALID_ERRORS = (
    "custom emoji identifier",
    "custom emoji id",
    "custom_emoji_id_invalid",
    "emoji_id_invalid",
    "icon_custom_emoji_id",
    "custom emoji document",
    "custom emoji is invalid",
)
CAPABILITY_TTL_SECONDS = 1800
BUTTON_ICON_MAP_TTL_SECONDS = 300

# Labels occasionally use emojis the icon library lacks; map them to the
# closest in-set icon so the button still renders a custom emoji.
LABEL_ICON_ALIASES = {
    "🔐": "🔒",
    "🛑": "🚫",
    "⛔": "🚫",
    "🎟": "🏷",
    "🆓": "🎁",
    "📋": "📄",
    "🆘": "❓",
    "🛜": "📶",
    "🚀": "🛜",
    "": "🎁",
    "🗒": "📄",
}


def _icon_lookup(emoji_map: dict[str, str], emoji: str) -> str | None:
    for candidate in (
        emoji,
        emoji.rstrip("\ufe0f"),
        LABEL_ICON_ALIASES.get(emoji),
        LABEL_ICON_ALIASES.get(emoji.rstrip("\ufe0f")),
    ):
        if candidate and (
            icon_id := emoji_map.get(candidate) or emoji_map.get(candidate.rstrip("\ufe0f"))
        ):
            return icon_id
    return None


def _needs_button_icons(markup: InlineKeyboardMarkup) -> bool:
    return any(
        not button.icon_custom_emoji_id and split_decorative_emoji(button.text or "")[0]
        for row in markup.inline_keyboard
        for button in row
    )


def with_button_icons[T](method: TelegramMethod[T], emoji_map: dict[str, str]) -> TelegramMethod[T]:
    """Promote leading decorative emojis in button labels to custom emoji icons."""
    markup = getattr(method, "reply_markup", None)
    if not isinstance(markup, InlineKeyboardMarkup):
        return method
    changed = False
    rows = []
    for row in markup.inline_keyboard:
        buttons = []
        for button in row:
            if not button.icon_custom_emoji_id:
                emoji, label = split_decorative_emoji(button.text or "")
                icon_id = _icon_lookup(emoji_map, emoji) if emoji else None
                if icon_id:
                    button = button.model_copy(
                        update={"icon_custom_emoji_id": icon_id, "text": label}
                    )
                    changed = True
            buttons.append(button)
        rows.append(buttons)
    if not changed:
        return method
    return method.model_copy(
        update={"reply_markup": markup.model_copy(update={"inline_keyboard": rows})}
    )


def custom_emoji_error(message: str) -> Literal["permission", "invalid"] | None:
    normalized = message.casefold()
    if any(value in normalized for value in _PERMISSION_ERRORS):
        return "permission"
    if any(value in normalized for value in _INVALID_ERRORS):
        return "invalid"
    return None


def method_features[T](method: TelegramMethod[T]) -> set[Literal["icon", "text"]]:
    features: set[Literal["icon", "text"]] = set()
    markup = getattr(method, "reply_markup", None)
    if isinstance(markup, InlineKeyboardMarkup) and any(
        button.icon_custom_emoji_id for row in markup.inline_keyboard for button in row
    ):
        features.add("icon")
    parse_mode = getattr(method, "parse_mode", None)
    html = parse_mode == "HTML" or isinstance(parse_mode, Default)
    if html and any(
        isinstance(value := getattr(method, key, None), str) and "tg-emoji" in value.lower()
        for key in ("text", "caption")
    ):
        features.add("text")
    if any(
        entity.type == "custom_emoji"
        for key in ("entities", "caption_entities")
        for entity in (getattr(method, key, None) or [])
    ):
        features.add("text")
    return features


def unicode_method[T](bot: Bot, method: TelegramMethod[T], features: Set[str]) -> TelegramMethod[T]:
    update: dict[str, object] = {}
    if "text" in features:
        for key in ("text", "caption"):
            value = getattr(method, key, None)
            if isinstance(value, str):
                update[key] = custom_emoji_unicode_html(value)
        for key in ("entities", "caption_entities"):
            entities = getattr(method, key, None)
            if entities:
                # Removing this entity preserves all UTF-16 offsets and the original fallback text.
                update[key] = [entity for entity in entities if entity.type != "custom_emoji"]
    markup = getattr(method, "reply_markup", None)
    if "icon" in features and isinstance(markup, InlineKeyboardMarkup):
        rows = []
        for row in markup.inline_keyboard:
            buttons = []
            for button in row:
                if button.icon_custom_emoji_id:
                    cached = read_item(bot.id, button.icon_custom_emoji_id)
                    fallback = cached.fallback if cached else "🙂"
                    prefix, _ = split_decorative_emoji(button.text)
                    text = button.text if prefix else f"{fallback} {button.text}"
                    button = button.model_copy(update={"icon_custom_emoji_id": None, "text": text})
                buttons.append(button)
            rows.append(buttons)
        update["reply_markup"] = markup.model_copy(update={"inline_keyboard": rows})
    return method.model_copy(update=update)


class CustomEmojiFallbackMiddleware(BaseRequestMiddleware):
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings
        self._icon_map_cache: tuple[float, dict[str, str]] | None = None

    async def _button_icon_map(self, bot: Bot) -> dict[str, str]:
        if self._settings is None:
            return {}
        try:
            library = parse_emoji_library(self._settings.TELEGRAM_CUSTOM_EMOJI_LIBRARY_JSON)
        except Exception:
            return {}
        if not library.sets and not library.manual_ids:
            return {}
        cached = self._icon_map_cache
        if cached and time.monotonic() - cached[0] < BUTTON_ICON_MAP_TTL_SECONDS:
            return cached[1]
        emoji_map: dict[str, str] = {}
        for name in library.sets:
            try:
                loaded = await load_set(bot, name)
            except Exception:
                continue
            for item in loaded.items:
                emoji_map.setdefault(item.fallback, item.id)
                if item.fallback.endswith("\ufe0f"):
                    emoji_map.setdefault(item.fallback.rstrip("\ufe0f"), item.id)
        if library.manual_ids:
            with contextlib.suppress(Exception):
                for item in await resolve_ids(bot, library.manual_ids):
                    emoji_map.setdefault(item.fallback, item.id)
        self._icon_map_cache = (time.monotonic(), emoji_map)
        return emoji_map

    async def _apply_button_icons(
        self, bot: Bot, method: TelegramMethod[TelegramType]
    ) -> TelegramMethod[TelegramType]:
        markup = getattr(method, "reply_markup", None)
        if not isinstance(markup, InlineKeyboardMarkup) or not _needs_button_icons(markup):
            return method
        try:
            emoji_map = await self._button_icon_map(bot)
        except Exception:
            logger.warning("button icon map unavailable", exc_info=True)
            return method
        if not emoji_map:
            return method
        return with_button_icons(method, emoji_map)

    async def _apply_text_emojis(
        self, bot: Bot, method: TelegramMethod[TelegramType]
    ) -> TelegramMethod[TelegramType]:
        """Wrap known Unicode emojis in ``text``/``caption`` into tg-emoji markup."""
        parse_mode = getattr(method, "parse_mode", None)
        if isinstance(parse_mode, Default):
            parse_mode = getattr(getattr(bot, "default", None), "parse_mode", None)
        if parse_mode != ParseMode.HTML:
            return method
        if getattr(method, "entities", None) or getattr(method, "caption_entities", None):
            # Explicit entities carry UTF-16 offsets that conversion would break.
            return method
        try:
            emoji_map = await self._button_icon_map(bot)
        except Exception:
            return method
        if not emoji_map:
            return method
        update: dict[str, object] = {}
        for key, limit in (("text", 4096), ("caption", 1024)):
            value = getattr(method, key, None)
            if not isinstance(value, str):
                continue
            converted = unicode_emoji_to_custom_html(value, emoji_map)
            # Telegram enforces the limit on the visible text; tg-emoji markup
            # around the same fallback glyph does not add visible characters.
            if converted != value and len(value) <= limit:
                update[key] = converted
        if not update:
            return method
        return method.model_copy(update=update)

    async def __call__(
        self,
        make_request: NextRequestMiddlewareType[TelegramType],
        bot: Bot,
        method: TelegramMethod[TelegramType],
    ) -> Response[TelegramType]:
        method = await self._apply_button_icons(bot, method)
        method = await self._apply_text_emojis(bot, method)
        features = method_features(method)
        if not features:
            return await make_request(bot, method)
        chat_id = getattr(method, "chat_id", None)
        private = isinstance(chat_id, int) and chat_id > 0
        if private and not CUSTOM_EMOJI_PROBE.get():
            state = await asyncio.to_thread(capabilities, bot.id)
            unavailable = set()
            for feature in features:
                value = getattr(state, feature)
                if value.state == "unavailable" and value.tested_at:
                    try:
                        tested = datetime.fromisoformat(value.tested_at)
                        if tested.tzinfo is None:
                            continue
                    except ValueError:
                        continue
                    if 0 <= (datetime.now(UTC) - tested).total_seconds() < CAPABILITY_TTL_SECONDS:
                        unavailable.add(feature)
            if unavailable:
                method = unicode_method(bot, method, unavailable)
                features -= unavailable
        try:
            response = await make_request(bot, method)
            if private and isinstance(response, Message):
                if "icon" in features and response.reply_markup is not None:
                    present = any(
                        button.icon_custom_emoji_id
                        for row in response.reply_markup.inline_keyboard
                        for button in row
                    )
                    await asyncio.to_thread(observe_capability, bot.id, "icon", present)
                if "text" in features and (
                    response.text is not None or response.caption is not None
                ):
                    present = any(
                        entity.type == "custom_emoji"
                        for entity in [
                            *(response.entities or []),
                            *(response.caption_entities or []),
                        ]
                    )
                    await asyncio.to_thread(observe_capability, bot.id, "text", present)
            return response
        except TelegramBadRequest as exc:
            reason = custom_emoji_error(exc.message)
            if not features or reason is None:
                raise
            if private and reason == "permission":
                for feature in features:
                    await asyncio.to_thread(observe_capability, bot.id, feature, False)
            # A rejected request delivered nothing. Retry once; unrelated errors propagate.
            return await make_request(bot, unicode_method(bot, method, features))
