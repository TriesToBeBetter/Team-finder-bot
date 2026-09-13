import logging
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from config.settings import settings
from bot.keyboards.reply import get_main_menu_keyboard
from bot.database.models import User

logger = logging.getLogger(__name__)

router = Router(name="common_router")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, db_user: User) -> None:
    """Handle /start command and render the main welcome menu."""
    await state.clear()
    is_admin = settings.is_admin(message.from_user.id) if message.from_user else False

    welcome_text = (
        "<b>👥 TeamFinder</b>\n\n"
        "<i>Найди людей для своей команды или найди команду для себя.</i>\n\n"
        "Выберите нужное действие в меню ниже:\n"
        "• <b>🔎 Найти команду</b> — если вы специалист и ищете проект или команду\n"
        "• <b>👥 Найти участника</b> — если вы собираете команду в свой проект\n"
        "• <b>📋 Моя анкета</b> — просмотр и управление вашей анкетой\n"
        "• <b>❓ Помощь</b> — как это устроено и правила сервиса"
    )

    await message.answer(
        welcome_text,
        reply_markup=get_main_menu_keyboard(is_admin=is_admin),
        parse_mode="HTML"
    )


@router.message(Command("help"))
@router.message(F.text == "❓ Помощь")
async def cmd_help(message: Message, state: FSMContext) -> None:
    """Provide detailed usage instructions and community rules."""
    help_text = (
        "<b>❓ О сервисе TeamFinder Bot</b>\n\n"
        "<b>Как это работает:</b>\n"
        "1. Выберите подходящий сценарий: поиск команды или поиск участника в проект.\n"
        "2. Ответьте на несколько коротких вопросов о роли, навыках и опыте.\n"
        "3. Проверьте сформированную анкету и подтвердите отправку.\n"
        "4. Анкета поступит администраторам сообщества на модерацию.\n"
        "5. После одобрения администратор свяжется с вами или добавит в команду!\n\n"
        "<b>Безопасность:</b>\n"
        "• Общение с администраторами может происходить прямо через бота.\n"
        "• Спам, реклама и оскорбления ведут к моментальной блокировке."
    )
    await message.answer(help_text, parse_mode="HTML")


@router.message(F.text == "❌ Отмена")
@router.callback_query(F.data == "app_cancel")
async def process_cancel(event: Message | CallbackQuery, state: FSMContext) -> None:
    """Cancel any active FSM flow and return to main menu."""
    await state.clear()
    user_id = event.from_user.id if event.from_user else 0
    is_admin = settings.is_admin(user_id)

    cancel_msg = "❌ Действие отменено. Вы вернулись в главное меню."
    if isinstance(event, CallbackQuery):
        await event.answer("Отменено")
        await event.message.answer(cancel_msg, reply_markup=get_main_menu_keyboard(is_admin=is_admin))
    else:
        await event.answer(cancel_msg, reply_markup=get_main_menu_keyboard(is_admin=is_admin))
