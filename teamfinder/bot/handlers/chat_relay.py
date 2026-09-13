import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from config.settings import settings
from bot.states.admin import AdminContactStates, UserReplyStates
from bot.keyboards.reply import get_main_menu_keyboard
from bot.keyboards.inline import get_user_reply_keyboard, InlineKeyboardMarkup, InlineKeyboardButton
from bot.database.session import get_session
from bot.services.application import get_application_by_id
from bot.services.chat import record_chat_message
from bot.utils.validators import validate_text_length
from bot.utils.formatters import escape

logger = logging.getLogger(__name__)

router = Router(name="chat_relay_router")


# ==========================================
# 1. Admin sends message to applicant
# ==========================================

@router.message(AdminContactStates.waiting_for_message)
async def process_admin_message_to_user(message: Message, state: FSMContext, bot: Bot) -> None:
    """Relay admin's message directly to the applicant via the bot."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отправка сообщения отменена.", reply_markup=get_main_menu_keyboard(is_admin=True))
        return

    valid, clean_text = validate_text_length(message.text or "", min_len=2, max_len=1500)
    if not valid:
        await message.answer(f"⚠️ {clean_text}")
        return

    data = await state.get_data()
    app_id = data.get("app_id")
    candidate_tg_id = data.get("candidate_tg_id")
    admin_id = message.from_user.id

    if not app_id or not candidate_tg_id:
        await state.clear()
        await message.answer("Ошибка контекста заявки. Попробуйте снова из меню заявки.", reply_markup=get_main_menu_keyboard(is_admin=True))
        return

    # Record message in database
    async with get_session() as session:
        await record_chat_message(
            session=session,
            application_id=app_id,
            sender_type="admin",
            sender_id=admin_id,
            recipient_id=candidate_tg_id,
            text=clean_text,
            telegram_message_id=message.message_id,
        )

    # Deliver to candidate
    outgoing_text = (
        "💬 <b>Сообщение от администратора:</b>\n\n"
        f"{escape(clean_text)}\n\n"
        "<i>Нажмите кнопку ниже, чтобы отправить ответ администратору прямо через бота:</i>"
    )

    try:
        await bot.send_message(
            chat_id=candidate_tg_id,
            text=outgoing_text,
            reply_markup=get_user_reply_keyboard(app_id),
            parse_mode="HTML"
        )
        await state.clear()
        await message.answer(
            f"✅ <b>Сообщение успешно доставлено кандидату (Заявка #{app_id})!</b>",
            reply_markup=get_main_menu_keyboard(is_admin=True),
            parse_mode="HTML"
        )
        logger.info(f"Relayed admin {admin_id} message to applicant {candidate_tg_id} for app #{app_id}")
    except Exception as e:
        logger.error(f"Failed to deliver relay message to user {candidate_tg_id}: {e}")
        await message.answer(
            f"⚠️ Не удалось доставить сообщение кандидату (возможно, бот заблокирован пользователем): {e}",
            reply_markup=get_main_menu_keyboard(is_admin=True)
        )
        await state.clear()


# ==========================================
# 2. Applicant replies back to admin
# ==========================================

@router.callback_query(F.data.startswith("user_reply:"))
async def process_user_start_reply(callback: CallbackQuery, state: FSMContext) -> None:
    """Prompt applicant to type a reply to the administrator."""
    app_id = int(callback.data.split(":")[1])

    await state.clear()
    await state.set_state(UserReplyStates.waiting_for_reply)
    await state.update_data(app_id=app_id)

    await callback.answer()
    await callback.message.answer(
        "✍️ <b>Напишите ваш ответ администратору:</b>\n\n"
        "Ваше сообщение будет безопасно передано модераторам через бота.",
        reply_markup=get_main_menu_keyboard(is_admin=settings.is_admin(callback.from_user.id)),
        parse_mode="HTML"
    )


@router.message(UserReplyStates.waiting_for_reply)
async def process_user_reply_message(message: Message, state: FSMContext, bot: Bot) -> None:
    """Receive applicant's reply and forward to the administrators."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Ответ отменен.", reply_markup=get_main_menu_keyboard(is_admin=False))
        return

    valid, clean_text = validate_text_length(message.text or "", min_len=2, max_len=1500)
    if not valid:
        await message.answer(f"⚠️ {clean_text}")
        return

    data = await state.get_data()
    app_id = data.get("app_id")
    user_id = message.from_user.id

    async with get_session() as session:
        app = await get_application_by_id(session, app_id)
        if not app:
            await state.clear()
            await message.answer("Анкета не найдена.", reply_markup=get_main_menu_keyboard(is_admin=False))
            return

        candidate_name = app.name
        # Determine target admin recipient
        target_admin_id = app.reviewed_by_admin_id or (list(settings.admin_ids)[0] if settings.admin_ids else None)

        # Store in database
        if target_admin_id:
            await record_chat_message(
                session=session,
                application_id=app_id,
                sender_type="user",
                sender_id=user_id,
                recipient_id=target_admin_id,
                text=clean_text,
                telegram_message_id=message.message_id,
            )

    # Deliver to administrators
    admin_relay_text = (
        f"💬 <b>Ответ от кандидата по заявке #{app_id} ({escape(candidate_name)}):</b>\n\n"
        f"{escape(clean_text)}"
    )

    admin_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💬 Ответить кандидату", callback_data=f"adm_contact:{app_id}")]
        ]
    )

    recipients = set(settings.admin_ids)
    if target_admin_id:
        recipients.add(target_admin_id)
    if settings.ADMIN_CHAT_ID:
        recipients.add(settings.ADMIN_CHAT_ID)

    delivered = 0
    for admin_tg in recipients:
        try:
            await bot.send_message(
                chat_id=admin_tg,
                text=admin_relay_text,
                reply_markup=admin_keyboard,
                parse_mode="HTML"
            )
            delivered += 1
        except Exception as e:
            logger.warning(f"Could not forward candidate reply to admin {admin_tg}: {e}")

    await state.clear()
    await message.answer(
        "✅ <b>Ваш ответ успешно передан администраторам!</b>",
        reply_markup=get_main_menu_keyboard(is_admin=settings.is_admin(user_id)),
        parse_mode="HTML"
    )
    logger.info(f"User {user_id} reply for app #{app_id} delivered to {delivered} admins.")
