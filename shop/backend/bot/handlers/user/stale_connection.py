import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.services.stale_connection_nudge import CLOSE_CALLBACK
from bot.utils.callback_answer import callback_message_or_none, safe_answer_callback

logger = logging.getLogger(__name__)

router = Router(name="stale_connection")


@router.callback_query(F.data == CLOSE_CALLBACK)
async def stale_connection_close_handler(callback: CallbackQuery):
    message = callback_message_or_none(callback)
    if message is not None:
        try:
            await message.delete()
        except Exception:
            logger.debug(
                "Failed to delete stale-connection nudge message %s",
                getattr(message, "message_id", None),
            )
    await safe_answer_callback(callback)
