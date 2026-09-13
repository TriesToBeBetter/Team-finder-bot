import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

from config.settings import settings
from bot.database.models import ApplicationStatus, User
from bot.database.session import get_session
from bot.services.user import get_platform_stats
from bot.services.application import list_applications, search_applications
from bot.utils.formatters import format_stats, format_admin_application, escape
from bot.keyboards.inline import get_admin_panel_keyboard, get_admin_application_keyboard
from bot.keyboards.reply import get_cancel_keyboard, get_main_menu_keyboard
from bot.states.admin import AdminSearchStates

logger = logging.getLogger(__name__)

router = Router(name="admin_panel_router")


@router.message(Command("admin"))
@router.message(F.text == "🛡 Админ-панель (/admin)")
async def cmd_admin(message: Message, state: FSMContext) -> None:
    """Access the admin dashboard (strictly checked by Telegram user_id)."""
    user_id = message.from_user.id if message.from_user else 0
    if not settings.is_admin(user_id):
        await message.answer("⛔️ <b>Доступ запрещен.</b> У вас нет прав администратора.", parse_mode="HTML")
        logger.warning(f"Unauthorized /admin attempt by user_id={user_id}")
        return

    await state.clear()
    async with get_session() as session:
        stats = await get_platform_stats(session)

    welcome_text = (
        "🛡 <b>Панель управления TeamFinder</b>\n\n"
        f"Добро пожаловать, администратор! Всего заявок: <b>{stats['total_apps']}</b> "
        f"(Новых: <b>{stats['new_apps']}</b>)\n\n"
        "Выберите действие:"
    )

    await message.answer(welcome_text, reply_markup=get_admin_panel_keyboard(), parse_mode="HTML")


@router.callback_query(F.data == "adm_stats")
async def process_adm_stats(callback: CallbackQuery) -> None:
    """Display platform metrics."""
    async with get_session() as session:
        stats = await get_platform_stats(session)

    text = format_stats(stats)
    await callback.answer()
    await callback.message.edit_text(text, reply_markup=get_admin_panel_keyboard(), parse_mode="HTML")


@router.callback_query(F.data == "adm_refresh")
async def process_adm_refresh(callback: CallbackQuery) -> None:
    """Refresh admin control panel."""
    await callback.answer("Данные обновлены")
    async with get_session() as session:
        stats = await get_platform_stats(session)

    welcome_text = (
        "🛡 <b>Панель управления TeamFinder</b>\n\n"
        f"Всего пользователей: <b>{stats['total_users']}</b>\n"
        f"Новых заявок: <b>{stats['new_apps']}</b>\n"
        f"Принятых: <b>{stats['accepted_apps']}</b>\n"
        f"Отклонённых: <b>{stats['rejected_apps']}</b>\n\n"
        "Выберите раздел:"
    )
    await callback.message.edit_text(welcome_text, reply_markup=get_admin_panel_keyboard(), parse_mode="HTML")


@router.callback_query(F.data.startswith("adm_list:"))
async def process_adm_list(callback: CallbackQuery) -> None:
    """List applications filtered by status or blocked users."""
    category = callback.data.split(":")[1]

    if category == "blocked":
        async with get_session() as session:
            stmt = select(User).where(User.is_blocked.is_(True)).limit(20)
            res = await session.execute(stmt)
            blocked_users = list(res.scalars().all())

        if not blocked_users:
            await callback.answer("Заблокированных пользователей нет.", show_alert=True)
            return

        text = "🚫 <b>Список заблокированных пользователей:</b>\n\n"
        for u in blocked_users:
            text += f"• <code>{u.telegram_user_id}</code> | @{u.username or 'без_username'} ({escape(u.first_name or '')})\n"
        await callback.answer()
        await callback.message.answer(text, parse_mode="HTML")
        return

    status_map = {
        "new": ApplicationStatus.NEW,
        "accepted": ApplicationStatus.ACCEPTED,
        "rejected": ApplicationStatus.REJECTED,
    }
    target_status = status_map.get(category)
    if not target_status:
        await callback.answer("Неизвестная категория", show_alert=True)
        return

    async with get_session() as session:
        apps = await list_applications(session, status=target_status, limit=5)

    if not apps:
        await callback.answer(f"Заявок со статусом '{target_status.value}' не найдено.", show_alert=True)
        return

    await callback.answer(f"Найдено: {len(apps)}")
    for app in apps:
        card_text = format_admin_application(app)
        keyboard = get_admin_application_keyboard(app.id, app.status)
        await callback.message.answer(card_text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "adm_search")
async def process_adm_search_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    """Prompt admin for search keyword."""
    await state.clear()
    await state.set_state(AdminSearchStates.waiting_for_query)
    await callback.answer()
    await callback.message.answer(
        "🔍 <b>Поиск заявок</b>\n\n"
        "Введите поисковый запрос (имя, навык, роль или ключевое слово):",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )


@router.message(AdminSearchStates.waiting_for_query)
async def process_adm_search_query(message: Message, state: FSMContext) -> None:
    """Execute search query over applications."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Поиск отменен.", reply_markup=get_main_menu_keyboard(is_admin=True))
        return

    query = (message.text or "").strip()
    if len(query) < 2:
        await message.answer("Запрос слишком короткий (минимум 2 символа). Попробуйте еще раз:")
        return

    async with get_session() as session:
        results = await search_applications(session, query=query, limit=5)

    await state.clear()
    if not results:
        await message.answer(
            f"🔍 По запросу <i>«{escape(query)}»</i> ничего не найдено.",
            reply_markup=get_main_menu_keyboard(is_admin=True),
            parse_mode="HTML"
        )
        return

    await message.answer(
        f"🔍 <b>Результаты поиска по запросу «{escape(query)}» ({len(results)}):</b>",
        parse_mode="HTML"
    )
    for app in results:
        card_text = format_admin_application(app)
        keyboard = get_admin_application_keyboard(app.id, app.status)
        await message.answer(card_text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "adm_settings")
async def process_adm_settings(callback: CallbackQuery) -> None:
    """Display current system settings."""
    text = (
        "⚙️ <b>Системные настройки:</b>\n\n"
        f"• Администраторов настроено: <b>{len(settings.admin_ids)}</b>\n"
        f"• База данных: <b>{'SQLite' if 'sqlite' in settings.DATABASE_URL else 'PostgreSQL'}</b>\n"
        f"• AI модуль (Gemini): <b>{'Подключен' if settings.GEMINI_API_KEY else 'Не настроен (опционально)'}</b>\n"
        f"• Логирование: <b>{settings.LOG_LEVEL}</b>"
    )
    await callback.answer()
    await callback.message.edit_text(text, reply_markup=get_admin_panel_keyboard(), parse_mode="HTML")
