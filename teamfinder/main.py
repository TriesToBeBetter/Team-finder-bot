import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config.settings import settings
from bot.database.session import init_db
from bot.middlewares.auth import UserBlockCheckMiddleware, AdminCheckMiddleware
from bot.middlewares.logging import StructuredLoggingMiddleware
from bot.handlers import register_all_handlers

# Configure structured logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("teamfinder.main")


async def main() -> None:
    """Main application lifecycle runner."""
    logger.info("Starting TeamFinder Bot...")

    # 1. Initialize Database
    try:
        await init_db()
    except Exception as e:
        logger.critical(f"Database initialization failed: {e}", exc_info=True)
        sys.exit(1)

    # 2. Check Bot Token
    if not settings.BOT_TOKEN or "123456789" in settings.BOT_TOKEN:
        logger.warning(
            "⚠️ BOT_TOKEN is not configured or using default placeholder! "
            "Please create a .env file and set a valid BOT_TOKEN obtained from @BotFather. "
            "Example: BOT_TOKEN=7123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        )

    # 3. Setup Bot & Dispatcher
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # 4. Attach Middlewares
    # Outer structured logging for all traffic
    dp.update.outer_middleware(StructuredLoggingMiddleware())

    # User block check and database user injection
    dp.message.middleware(UserBlockCheckMiddleware())
    dp.callback_query.middleware(UserBlockCheckMiddleware())

    # Admin access check middleware
    dp.message.middleware(AdminCheckMiddleware())
    dp.callback_query.middleware(AdminCheckMiddleware())

    # 5. Register Handler Routers
    register_all_handlers(dp)

    logger.info(f"TeamFinder Bot initialized successfully. Configured admins: {list(settings.admin_ids)}")

    # 6. Start Polling
    try:
        # Drop pending updates on startup to prevent flooding from downtime
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Bot is now polling for Telegram updates...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.error(f"Polling loop stopped with error: {e}", exc_info=True)
    finally:
        logger.info("Shutting down bot session...")
        await bot.session.close()
        logger.info("Bot session closed successfully.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("TeamFinder Bot terminated by user/system.")
