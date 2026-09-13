import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.database.models import User, ApplicationStatus
from bot.database.session import get_session
from bot.services.application import get_active_application, cancel_application
from bot.utils.formatters import format_user_profile
from bot.keyboards.inline import get_my_profile_keyboard
from bot.keyboards.reply import get_main_menu_keyboard
from config.settings import settings

logger = logging.getLogger(__name__)

router = Router(name="my_profile_router")


@router.message(F.text == "📋 Моя анкета")
async def show_my_profile(message: Message, state: FSMContext, db_user: User) -> None:
    """Render the user's active application and actions."""
    await state.clear()
    async with get_session() as session:
        active_app = await get_active_application(session, db_user.id)

    if not active_app:
        text = (
            "<b>📋 У вас пока нет активной анкеты.</b>\n\n"
            "Вы можете создать новую анкету прямо сейчас:\n"
            "• <b>🔎 Найти команду</b> — если вы ищете проект\n"
            "• <b>👥 Найти участника</b> — если вам нужен человек в команду"
        )
        await message.answer(text, reply_markup=get_my_profile_keyboard(has_active_application=False), parse_mode="HTML")
        return

    text = format_user_profile(active_app)
    await message.answer(
        text,
        reply_markup=get_my_profile_keyboard(has_active_application=True, app_id=active_app.id),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("prof_delete:"))
async def process_delete_profile(callback: CallbackQuery, db_user: User) -> None:
    """User cancels / deletes their existing application."""
    app_id = int(callback.data.split(":")[1])
    async with get_session() as session:
        success = await cancel_application(session, app_id, db_user.id)

    if success:
        await callback.answer("Анкета удалена", show_alert=False)
        is_admin = settings.is_admin(callback.from_user.id)
        await callback.message.edit_text(
            "🗑 <b>Ваша анкета была успешно отозвана / удалена.</b>\n\n"
            "Теперь вы можете в любой момент заполнить новую анкету.",
            reply_markup=get_my_profile_keyboard(has_active_application=False),
            parse_mode="HTML"
        )
    else:
        await callback.answer("Не удалось удалить анкету или она уже неактивна.", show_alert=True)


@router.callback_query(F.data.startswith("prof_edit:"))
async def process_edit_profile(callback: CallbackQuery, db_user: User) -> None:
    """User wants to edit: cancel previous active and prompt to start fresh."""
    app_id = int(callback.data.split(":")[1])
    async with get_session() as session:
        await cancel_application(session, app_id, db_user.id)

    await callback.answer()
    await callback.message.edit_text(
        "✏️ Предыдущая анкета архивирована. Выберите тип новой анкеты:",
        reply_markup=get_my_profile_keyboard(has_active_application=False)
    )


@router.callback_query(F.data == "prof_back_main")
async def process_back_main(callback: CallbackQuery) -> None:
    """Return to main menu."""
    await callback.answer()
    is_admin = settings.is_admin(callback.from_user.id)
    await callback.message.answer(
        "Главное меню:",
        reply_markup=get_main_menu_keyboard(is_admin=is_admin)
    )
