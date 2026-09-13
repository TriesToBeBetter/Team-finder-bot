import logging
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

from config.settings import settings
from bot.database.session import get_session
from bot.services.user import is_user_blocked, get_or_create_user

logger = logging.getLogger(__name__)


class UserBlockCheckMiddleware(BaseMiddleware):
    """
    Middleware verifying if the user is registered and checking whether
    they are blocked before allowing any interactions.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user_tg = getattr(event, "from_user", None)
        if not user_tg:
            return await handler(event, data)

        async with get_session() as session:
            # Register or update user record
            db_user = await get_or_create_user(
                session=session,
                telegram_user_id=user_tg.id,
                username=user_tg.username,
                first_name=user_tg.first_name,
            )
            data["db_user"] = db_user

            # Check if user is blocked
            if db_user.is_blocked:
                # Do not notify repeatedly on silent callbacks, but notify on user messages
                if isinstance(event, Message):
                    await event.answer(
                        "🚫 <b>Ваш аккаунт заблокирован администрацией бота.</b>\n"
                        "Вы не можете отправлять новые анкеты и взаимодействовать с сервисом.",
                        parse_mode="HTML"
                    )
                elif isinstance(event, CallbackQuery):
                    await event.answer("🚫 Ваш аккаунт заблокирован администратором.", show_alert=True)
                return None

        return await handler(event, data)


class AdminCheckMiddleware(BaseMiddleware):
    """
    Middleware verifying admin permissions for /admin commands and adm_* callback queries.
    Never relies on usernames; strictly checks Telegram user_id against settings.admin_ids.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user_tg = getattr(event, "from_user", None)
        if not user_tg:
            return await handler(event, data)

        is_admin = settings.is_admin(user_tg.id)
        data["is_admin"] = is_admin

        # If it is an admin callback query (adm_*)
        if isinstance(event, CallbackQuery) and event.data and event.data.startswith("adm_"):
            if not is_admin:
                logger.warning(f"Unauthorized admin callback attempt from tg_id={user_tg.id}")
                await event.answer("⛔️ У вас нет прав администратора для этого действия.", show_alert=True)
                return None

        return await handler(event, data)
