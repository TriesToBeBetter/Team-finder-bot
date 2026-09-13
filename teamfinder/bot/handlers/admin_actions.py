import logging
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.database.models import ApplicationStatus
from bot.database.session import get_session
from bot.services.application import get_application_by_id, update_application_status
from bot.services.user import set_user_block_status
from bot.keyboards.inline import get_admin_application_keyboard
from bot.keyboards.reply import get_cancel_keyboard
from bot.states.admin import AdminContactStates
from bot.utils.formatters import format_admin_application

logger = logging.getLogger(__name__)

router = Router(name="admin_actions_router")


@router.callback_query(F.data.startswith("adm_accept:"))
async def process_admin_accept(callback: CallbackQuery, bot: Bot) -> None:
    """Accept an application and notify the candidate."""
    app_id = int(callback.data.split(":")[1])
    admin_id = callback.from_user.id

    async with get_session() as session:
        success, app, msg = await update_application_status(
            session=session,
            app_id=app_id,
            new_status=ApplicationStatus.ACCEPTED,
            admin_id=admin_id,
        )
        if not success:
            await callback.answer(msg, show_alert=True)
            return

        candidate_tg_id = app.user.telegram_user_id
        app_name = app.name

    # 1. Update message in admin chat
    try:
        updated_keyboard = get_admin_application_keyboard(app_id, ApplicationStatus.ACCEPTED)
        async with get_session() as session:
            refreshed = await get_application_by_id(session, app_id)
            updated_text = format_admin_application(refreshed)
        await callback.message.edit_text(updated_text, reply_markup=updated_keyboard, parse_mode="HTML")
    except Exception as e:
        logger.warning(f"Failed to edit admin card message for #{app_id}: {e}")

    await callback.answer("✅ Анкета принята!", show_alert=False)

    # 2. Notify applicant
    user_notice = (
        "🎉 <b>Ваша анкета была принята!</b>\n\n"
        "Администратор скоро свяжется с вами для обсуждения деталей."
    )
    try:
        await bot.send_message(chat_id=candidate_tg_id, text=user_notice, parse_mode="HTML")
        logger.info(f"Accepted notification sent to applicant tg_id={candidate_tg_id} for app #{app_id}")
    except Exception as e:
        logger.error(f"Could not deliver acceptance notice to tg_id={candidate_tg_id}: {e}")


@router.callback_query(F.data.startswith("adm_reject:"))
async def process_admin_reject(callback: CallbackQuery, bot: Bot) -> None:
    """Reject an application and notify the candidate."""
    app_id = int(callback.data.split(":")[1])
    admin_id = callback.from_user.id

    async with get_session() as session:
        success, app, msg = await update_application_status(
            session=session,
            app_id=app_id,
            new_status=ApplicationStatus.REJECTED,
            admin_id=admin_id,
        )
        if not success:
            await callback.answer(msg, show_alert=True)
            return

        candidate_tg_id = app.user.telegram_user_id

    # 1. Update message in admin chat
    try:
        updated_keyboard = get_admin_application_keyboard(app_id, ApplicationStatus.REJECTED)
        async with get_session() as session:
            refreshed = await get_application_by_id(session, app_id)
            updated_text = format_admin_application(refreshed)
        await callback.message.edit_text(updated_text, reply_markup=updated_keyboard, parse_mode="HTML")
    except Exception as e:
        logger.warning(f"Failed to edit admin card message for #{app_id}: {e}")

    await callback.answer("❌ Анкета отклонена", show_alert=False)

    # 2. Notify applicant without internal comments
    user_notice = (
        "Спасибо за заявку!\n\n"
        "К сожалению, сейчас ваша анкета не подходит."
    )
    try:
        await bot.send_message(chat_id=candidate_tg_id, text=user_notice, parse_mode="HTML")
        logger.info(f"Rejection notification sent to applicant tg_id={candidate_tg_id} for app #{app_id}")
    except Exception as e:
        logger.error(f"Could not deliver rejection notice to tg_id={candidate_tg_id}: {e}")


@router.callback_query(F.data.startswith("adm_contact:"))
async def process_admin_contact(callback: CallbackQuery, state: FSMContext) -> None:
    """Initiate message prompt from admin to applicant."""
    app_id = int(callback.data.split(":")[1])

    async with get_session() as session:
        app = await get_application_by_id(session, app_id)
        if not app:
            await callback.answer("Анкета не найдена.", show_alert=True)
            return
        candidate_name = app.name

    await state.clear()
    await state.set_state(AdminContactStates.waiting_for_message)
    await state.update_data(app_id=app_id, candidate_tg_id=app.user.telegram_user_id)

    await callback.answer()
    await callback.message.answer(
        f"💬 <b>Напишите сообщение для кандидата {candidate_name} (Заявка #{app_id}):</b>\n\n"
        f"Бот передаст ваше сообщение кандидату и предоставит кнопку для ответа.",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("adm_block:"))
async def process_admin_block(callback: CallbackQuery, bot: Bot) -> None:
    """Block user and archive their applications."""
    app_id = int(callback.data.split(":")[1])
    admin_id = callback.from_user.id

    async with get_session() as session:
        app = await get_application_by_id(session, app_id)
        if not app:
            await callback.answer("Анкета не найдена.", show_alert=True)
            return

        candidate_tg_id = app.user.telegram_user_id
        await set_user_block_status(session, candidate_tg_id, blocked=True, admin_id=admin_id)
        # Update application status to rejected if new
        if app.status == ApplicationStatus.NEW:
            await update_application_status(session, app_id, ApplicationStatus.REJECTED, admin_id, "User blocked")

    try:
        updated_keyboard = get_admin_application_keyboard(app_id, ApplicationStatus.REJECTED)
        async with get_session() as session:
            refreshed = await get_application_by_id(session, app_id)
            updated_text = format_admin_application(refreshed) + "\n\n🚫 <b>ПОЛЬЗОВАТЕЛЬ ЗАБЛОКИРОВАН</b>"
        await callback.message.edit_text(updated_text, reply_markup=updated_keyboard, parse_mode="HTML")
    except Exception as e:
        logger.warning(f"Could not edit admin card on block for #{app_id}: {e}")

    await callback.answer("🚫 Пользователь успешно заблокирован.", show_alert=True)


@router.callback_query(F.data.startswith("adm_noop:"))
async def process_admin_noop(callback: CallbackQuery) -> None:
    """Status pill click handler: acknowledge without state changes."""
    await callback.answer("Статус заявки зафиксирован.")
