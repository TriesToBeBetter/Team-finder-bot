from aiogram import Dispatcher
from .common import router as common_router
from .questionnaire import router as questionnaire_router
from .my_profile import router as my_profile_router
from .admin_actions import router as admin_actions_router
from .chat_relay import router as chat_relay_router
from .admin import router as admin_router


def register_all_handlers(dp: Dispatcher) -> None:
    """Register all modular handler routers with the aiogram Dispatcher in prioritized order."""
    dp.include_router(common_router)
    dp.include_router(admin_router)
    dp.include_router(admin_actions_router)
    dp.include_router(chat_relay_router)
    dp.include_router(my_profile_router)
    dp.include_router(questionnaire_router)
