import logging
import time
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

logger = logging.getLogger("teamfinder.traffic")


class StructuredLoggingMiddleware(BaseMiddleware):
    """
    Structured logging middleware capturing incoming actions, execution time,
    and user IDs without leaking secrets.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        start_time = time.perf_counter()
        user_tg = getattr(event, "from_user", None)
        user_id = user_tg.id if user_tg else 0
        username = f"@{user_tg.username}" if user_tg and user_tg.username else "no_username"

        event_desc = "unknown"
        if isinstance(event, Message):
            event_desc = f"Message(text='{event.text[:30] if event.text else ''}...')"
        elif isinstance(event, CallbackQuery):
            event_desc = f"CallbackQuery(data='{event.data}')"

        logger.debug(f"Incoming [{user_id}|{username}]: {event_desc}")

        try:
            result = await handler(event, data)
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.debug(f"Completed [{user_id}]: {event_desc} in {duration_ms:.1f}ms")
            return result
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(f"Error handling [{user_id}]: {event_desc} after {duration_ms:.1f}ms: {e}", exc_info=True)
            raise
