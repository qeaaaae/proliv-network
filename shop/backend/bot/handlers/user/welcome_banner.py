"""Welcome message renderer.

Sends the branded photo card (`/app/data/branding/welcome.png`, shared
shop-data volume) with the welcome text as caption; falls back to plain
text when the file is missing. See `menu_card.py` for the shared card
machinery used by the whole user-facing navigation.
"""

from aiogram import Bot

from .menu_card import send_card


async def send_welcome_message(bot: Bot, chat_id: int, text: str) -> None:
    await send_card(bot, chat_id, text)
