import logging
from typing import Dict, Any
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from config.settings import settings
from bot.states.questionnaire import TeamSearchStates, MemberSearchStates
from bot.keyboards.reply import get_step_navigation_keyboard, get_main_menu_keyboard
from bot.keyboards.inline import get_confirm_keyboard, get_admin_application_keyboard
from bot.utils.validators import validate_text_length
from bot.utils.formatters import format_user_preview, format_admin_application
from bot.database.models import User, ApplicationType, ApplicationStatus
from bot.database.session import get_session
from bot.services.application import create_application, get_active_application

logger = logging.getLogger(__name__)

router = Router(name="questionnaire_router")


# ==========================================
# 1. Start Questionnaire ("Найти команду" & "Найти участника")
# ==========================================

@router.message(F.text == "🔎 Найти команду")
@router.callback_query(F.data == "start_team_search")
async def start_team_search(event: Message | CallbackQuery, state: FSMContext, db_user: User) -> None:
    """Initiate specialist resume filling flow."""
    async with get_session() as session:
        active_app = await get_active_application(session, db_user.id)
        if active_app:
            warning = (
                f"⚠️ У вас уже есть активная анкета <b>#{active_app.id}</b>!\n"
                f"Статус: <b>{active_app.status.value}</b>.\n\n"
                f"Вы можете просмотреть, отредактировать или удалить её в разделе <b>«📋 Моя анкета»</b>."
            )
            if isinstance(event, CallbackQuery):
                await event.answer()
                await event.message.answer(warning, parse_mode="HTML")
            else:
                await event.answer(warning, parse_mode="HTML")
            return

    await state.clear()
    await state.set_state(TeamSearchStates.name)
    prompt = (
        "<b>Шаг 1 из 7: Представьтесь</b>\n\n"
        "👤 Введите ваше имя или никнейм, как к вам обращаться:"
    )
    if isinstance(event, CallbackQuery):
        await event.answer()
        await event.message.answer(prompt, reply_markup=get_step_navigation_keyboard(), parse_mode="HTML")
    else:
        await event.answer(prompt, reply_markup=get_step_navigation_keyboard(), parse_mode="HTML")


@router.message(F.text == "👥 Найти участника")
@router.callback_query(F.data == "start_member_search")
async def start_member_search(event: Message | CallbackQuery, state: FSMContext, db_user: User) -> None:
    """Initiate project team-member recruitment flow."""
    async with get_session() as session:
        active_app = await get_active_application(session, db_user.id)
        if active_app:
            warning = (
                f"⚠️ У вас уже есть активная анкета <b>#{active_app.id}</b>!\n"
                f"Статус: <b>{active_app.status.value}</b>.\n\n"
                f"Вы можете просмотреть, отредактировать или удалить её в разделе <b>«📋 Моя анкета»</b>."
            )
            if isinstance(event, CallbackQuery):
                await event.answer()
                await event.message.answer(warning, parse_mode="HTML")
            else:
                await event.answer(warning, parse_mode="HTML")
            return

    await state.clear()
    await state.set_state(MemberSearchStates.name)
    prompt = (
        "<b>Шаг 1 из 7: Проект / Команда</b>\n\n"
        "🚀 Введите название вашего проекта или ваше имя/команду:"
    )
    if isinstance(event, CallbackQuery):
        await event.answer()
        await event.message.answer(prompt, reply_markup=get_step_navigation_keyboard(), parse_mode="HTML")
    else:
        await event.answer(prompt, reply_markup=get_step_navigation_keyboard(), parse_mode="HTML")


# ==========================================
# 2. TeamSearch Flow (Специалист ищет команду)
# ==========================================

@router.message(TeamSearchStates.name)
async def process_team_name(message: Message, state: FSMContext) -> None:
    if message.text == "⬅️ Назад":
        await message.answer("Вы в начале анкеты.", reply_markup=get_step_navigation_keyboard())
        return
    valid, text_or_err = validate_text_length(message.text or "", min_len=2, max_len=80)
    if not valid:
        await message.answer(f"⚠️ {text_or_err}")
        return

    await state.update_data(name=text_or_err)
    await state.set_state(TeamSearchStates.role)
    await message.answer(
        "<b>Шаг 2 из 7: Ваша роль</b>\n\n"
        "🎯 Укажите вашу специальность (например: <i>Frontend Developer, Python Backend, UI/UX Designer, QA, PM</i>):",
        reply_markup=get_step_navigation_keyboard(),
        parse_mode="HTML"
    )


@router.message(TeamSearchStates.role)
async def process_team_role(message: Message, state: FSMContext) -> None:
    if message.text == "⬅️ Назад":
        await state.set_state(TeamSearchStates.name)
        await message.answer("👤 Введите ваше имя или никнейм:", reply_markup=get_step_navigation_keyboard())
        return
    valid, text_or_err = validate_text_length(message.text or "", min_len=2, max_len=100)
    if not valid:
        await message.answer(f"⚠️ {text_or_err}")
        return

    await state.update_data(role=text_or_err)
    await state.set_state(TeamSearchStates.skills)
    await message.answer(
        "<b>Шаг 3 из 7: Ваши ключевые навыки</b>\n\n"
        "💻 Перечислите стек технологий и инструментов (например: <i>React, TypeScript, Tailwind, Git, REST API</i>):",
        reply_markup=get_step_navigation_keyboard(),
        parse_mode="HTML"
    )


@router.message(TeamSearchStates.skills)
async def process_team_skills(message: Message, state: FSMContext) -> None:
    if message.text == "⬅️ Назад":
        await state.set_state(TeamSearchStates.role)
        await message.answer("🎯 Укажите вашу специальность:", reply_markup=get_step_navigation_keyboard())
        return
    valid, text_or_err = validate_text_length(message.text or "", min_len=2, max_len=300)
    if not valid:
        await message.answer(f"⚠️ {text_or_err}")
        return

    await state.update_data(skills=text_or_err)
    await state.set_state(TeamSearchStates.experience)
    await message.answer(
        "<b>Шаг 4 из 7: Опыт</b>\n\n"
        "📈 Опишите ваш опыт (например: <i>2 года, Junior+, Middle, 3 завершенных проекта</i>):",
        reply_markup=get_step_navigation_keyboard(),
        parse_mode="HTML"
    )


@router.message(TeamSearchStates.experience)
async def process_team_experience(message: Message, state: FSMContext) -> None:
    if message.text == "⬅️ Назад":
        await state.set_state(TeamSearchStates.skills)
        await message.answer("💻 Перечислите стек технологий:", reply_markup=get_step_navigation_keyboard())
        return
    valid, text_or_err = validate_text_length(message.text or "", min_len=2, max_len=100)
    if not valid:
        await message.answer(f"⚠️ {text_or_err}")
        return

    await state.update_data(experience=text_or_err)
    await state.set_state(TeamSearchStates.looking_for)
    await message.answer(
        "<b>Шаг 5 из 7: Что вы ищете</b>\n\n"
        "🔎 Опишите, какую команду или проект вы ищете (например: <i>стартап с нуля, команду на хакатон, коммерческий пет-проект</i>):",
        reply_markup=get_step_navigation_keyboard(),
        parse_mode="HTML"
    )


@router.message(TeamSearchStates.looking_for)
async def process_team_looking_for(message: Message, state: FSMContext) -> None:
    if message.text == "⬅️ Назад":
        await state.set_state(TeamSearchStates.experience)
        await message.answer("📈 Опишите ваш опыт:", reply_markup=get_step_navigation_keyboard())
        return
    valid, text_or_err = validate_text_length(message.text or "", min_len=3, max_len=300)
    if not valid:
        await message.answer(f"⚠️ {text_or_err}")
        return

    await state.update_data(looking_for=text_or_err)
    await state.set_state(TeamSearchStates.availability)
    await message.answer(
        "<b>Шаг 6 из 7: Готовность по времени</b>\n\n"
        "⏰ Сколько времени готовы уделять (например: <i>10 часов в неделю, full-time, вечера и выходные</i>):",
        reply_markup=get_step_navigation_keyboard(),
        parse_mode="HTML"
    )


@router.message(TeamSearchStates.availability)
async def process_team_availability(message: Message, state: FSMContext) -> None:
    if message.text == "⬅️ Назад":
        await state.set_state(TeamSearchStates.looking_for)
        await message.answer("🔎 Опишите, какую команду вы ищете:", reply_markup=get_step_navigation_keyboard())
        return
    valid, text_or_err = validate_text_length(message.text or "", min_len=2, max_len=100)
    if not valid:
        await message.answer(f"⚠️ {text_or_err}")
        return

    await state.update_data(availability=text_or_err)
    await state.set_state(TeamSearchStates.about)
    await message.answer(
        "<b>Шаг 7 из 7: О себе</b>\n\n"
        "📝 Расскажите дополнительно о себе, ваших сильных сторонах, или прикрепите ссылку на портфолио/GitHub (если нечего добавить, отправьте '-'):",
        reply_markup=get_step_navigation_keyboard(),
        parse_mode="HTML"
    )


@router.message(TeamSearchStates.about)
async def process_team_about(message: Message, state: FSMContext) -> None:
    if message.text == "⬅️ Назад":
        await state.set_state(TeamSearchStates.availability)
        await message.answer("⏰ Сколько времени готовы уделять:", reply_markup=get_step_navigation_keyboard())
        return

    about_text = message.text or ""
    if about_text.strip() == "-":
        about_text = ""
    else:
        valid, text_or_err = validate_text_length(about_text, min_len=1, max_len=600)
        if not valid:
            await message.answer(f"⚠️ {text_or_err}")
            return
        about_text = text_or_err

    user_contact = f"@{message.from_user.username}" if message.from_user.username else f"ID: {message.from_user.id}"
    await state.update_data(
        about=about_text,
        telegram_contact=user_contact,
        app_type=ApplicationType.LOOKING_FOR_TEAM.value,
    )
    await state.set_state(TeamSearchStates.confirm)

    data = await state.get_data()
    preview_text = format_user_preview(data, ApplicationType.LOOKING_FOR_TEAM)
    await message.answer(preview_text, reply_markup=get_confirm_keyboard(), parse_mode="HTML")


# ==========================================
# 3. MemberSearch Flow (Проект ищет участника)
# ==========================================

@router.message(MemberSearchStates.name)
async def process_member_name(message: Message, state: FSMContext) -> None:
    if message.text == "⬅️ Назад":
        await message.answer("Вы в начале создания заявки.", reply_markup=get_step_navigation_keyboard())
        return
    valid, text_or_err = validate_text_length(message.text or "", min_len=2, max_len=80)
    if not valid:
        await message.answer(f"⚠️ {text_or_err}")
        return

    await state.update_data(name=text_or_err)
    await state.set_state(MemberSearchStates.role)
    await message.answer(
        "<b>Шаг 2 из 7: Кого вы ищете</b>\n\n"
        "🎯 Какая роль требуется в проект? (например: <i>Python-разработчик, UI/UX Designer, DevOps инженер</i>):",
        reply_markup=get_step_navigation_keyboard(),
        parse_mode="HTML"
    )


@router.message(MemberSearchStates.role)
async def process_member_role(message: Message, state: FSMContext) -> None:
    if message.text == "⬅️ Назад":
        await state.set_state(MemberSearchStates.name)
        await message.answer("🚀 Введите название вашего проекта или ваше имя:", reply_markup=get_step_navigation_keyboard())
        return
    valid, text_or_err = validate_text_length(message.text or "", min_len=2, max_len=100)
    if not valid:
        await message.answer(f"⚠️ {text_or_err}")
        return

    await state.update_data(role=text_or_err)
    await state.set_state(MemberSearchStates.skills)
    await message.answer(
        "<b>Шаг 3 из 7: Требуемые навыки</b>\n\n"
        "💻 Какие технологии должен знать кандидат? (например: <i>Python, aiogram, PostgreSQL, Docker</i>):",
        reply_markup=get_step_navigation_keyboard(),
        parse_mode="HTML"
    )


@router.message(MemberSearchStates.skills)
async def process_member_skills(message: Message, state: FSMContext) -> None:
    if message.text == "⬅️ Назад":
        await state.set_state(MemberSearchStates.role)
        await message.answer("🎯 Какая роль требуется в проект?:", reply_markup=get_step_navigation_keyboard())
        return
    valid, text_or_err = validate_text_length(message.text or "", min_len=2, max_len=300)
    if not valid:
        await message.answer(f"⚠️ {text_or_err}")
        return

    await state.update_data(skills=text_or_err)
    await state.set_state(MemberSearchStates.experience)
    await message.answer(
        "<b>Шаг 4 из 7: Требуемый опыт</b>\n\n"
        "📈 Какой уровень опыта ожидается? (например: <i>от 1 года, Middle, готовы взять начинающего с горящими глазами</i>):",
        reply_markup=get_step_navigation_keyboard(),
        parse_mode="HTML"
    )


@router.message(MemberSearchStates.experience)
async def process_member_experience(message: Message, state: FSMContext) -> None:
    if message.text == "⬅️ Назад":
        await state.set_state(MemberSearchStates.skills)
        await message.answer("💻 Какие технологии должен знать кандидат?:", reply_markup=get_step_navigation_keyboard())
        return
    valid, text_or_err = validate_text_length(message.text or "", min_len=2, max_len=100)
    if not valid:
        await message.answer(f"⚠️ {text_or_err}")
        return

    await state.update_data(experience=text_or_err)
    await state.set_state(MemberSearchStates.project_description)
    await message.answer(
        "<b>Шаг 5 из 7: Описание проекта</b>\n\n"
        "📖 Расскажите подробнее о проекте (например: <i>Делаем небольшой игровой проект на Telegram Mini Apps, стадия MVP</i>):",
        reply_markup=get_step_navigation_keyboard(),
        parse_mode="HTML"
    )


@router.message(MemberSearchStates.project_description)
async def process_member_project_desc(message: Message, state: FSMContext) -> None:
    if message.text == "⬅️ Назад":
        await state.set_state(MemberSearchStates.experience)
        await message.answer("📈 Какой уровень опыта ожидается?:", reply_markup=get_step_navigation_keyboard())
        return
    valid, text_or_err = validate_text_length(message.text or "", min_len=3, max_len=500)
    if not valid:
        await message.answer(f"⚠️ {text_or_err}")
        return

    await state.update_data(project_description=text_or_err, looking_for=text_or_err)
    await state.set_state(MemberSearchStates.availability)
    await message.answer(
        "<b>Шаг 6 из 7: Занятость</b>\n\n"
        "⏰ Сколько времени потребуется уделять? (например: <i>10-15 часов в неделю, свободный график</i>):",
        reply_markup=get_step_navigation_keyboard(),
        parse_mode="HTML"
    )


@router.message(MemberSearchStates.availability)
async def process_member_availability(message: Message, state: FSMContext) -> None:
    if message.text == "⬅️ Назад":
        await state.set_state(MemberSearchStates.project_description)
        await message.answer("📖 Расскажите подробнее о проекте:", reply_markup=get_step_navigation_keyboard())
        return
    valid, text_or_err = validate_text_length(message.text or "", min_len=2, max_len=100)
    if not valid:
        await message.answer(f"⚠️ {text_or_err}")
        return

    await state.update_data(availability=text_or_err)
    await state.set_state(MemberSearchStates.about)
    await message.answer(
        "<b>Шаг 7 из 7: Условия и дополнительно</b>\n\n"
        "📝 Условия сотрудничества, доля, оплата или пожелания (если нечего добавить, отправьте '-'):",
        reply_markup=get_step_navigation_keyboard(),
        parse_mode="HTML"
    )


@router.message(MemberSearchStates.about)
async def process_member_about(message: Message, state: FSMContext) -> None:
    if message.text == "⬅️ Назад":
        await state.set_state(MemberSearchStates.availability)
        await message.answer("⏰ Сколько времени потребуется уделять?:", reply_markup=get_step_navigation_keyboard())
        return

    about_text = message.text or ""
    if about_text.strip() == "-":
        about_text = ""
    else:
        valid, text_or_err = validate_text_length(about_text, min_len=1, max_len=600)
        if not valid:
            await message.answer(f"⚠️ {text_or_err}")
            return
        about_text = text_or_err

    user_contact = f"@{message.from_user.username}" if message.from_user.username else f"ID: {message.from_user.id}"
    await state.update_data(
        about=about_text,
        telegram_contact=user_contact,
        app_type=ApplicationType.LOOKING_FOR_MEMBER.value,
    )
    await state.set_state(MemberSearchStates.confirm)

    data = await state.get_data()
    preview_text = format_user_preview(data, ApplicationType.LOOKING_FOR_MEMBER)
    await message.answer(preview_text, reply_markup=get_confirm_keyboard(), parse_mode="HTML")


# ==========================================
# 4. Confirmation / Edit / Submit Handlers
# ==========================================

@router.callback_query(F.data == "app_edit")
async def process_app_edit(callback: CallbackQuery, state: FSMContext) -> None:
    """Allow user to restart or modify their draft questionnaire."""
    data = await state.get_data()
    app_type_val = data.get("app_type", ApplicationType.LOOKING_FOR_TEAM.value)

    if app_type_val == ApplicationType.LOOKING_FOR_TEAM.value:
        await state.set_state(TeamSearchStates.name)
        await callback.answer("Редактирование")
        await callback.message.answer(
            "✏️ Начнем редактирование заново.\n\n👤 Введите ваше имя или никнейм:",
            reply_markup=get_step_navigation_keyboard()
        )
    else:
        await state.set_state(MemberSearchStates.name)
        await callback.answer("Редактирование")
        await callback.message.answer(
            "✏️ Начнем редактирование заново.\n\n🚀 Введите название вашего проекта:",
            reply_markup=get_step_navigation_keyboard()
        )


@router.callback_query(F.data == "app_submit")
async def process_app_submit(callback: CallbackQuery, state: FSMContext, bot: Bot, db_user: User) -> None:
    """Commit application to DB and safely broadcast card to administrators."""
    data = await state.get_data()
    if not data or not data.get("name"):
        await callback.answer("Ошибка данных. Пожалуйста, заполните анкету заново.", show_alert=True)
        await state.clear()
        return

    app_type_enum = ApplicationType(data.get("app_type", ApplicationType.LOOKING_FOR_TEAM.value))

    async with get_session() as session:
        # Double check that user is not blocked
        if db_user.is_blocked:
            await callback.answer("🚫 Вы заблокированы и не можете отправлять анкеты.", show_alert=True)
            await state.clear()
            return

        # Double check no active application exists
        existing = await get_active_application(session, db_user.id)
        if existing:
            await callback.answer("У вас уже есть активная анкета!", show_alert=True)
            await state.clear()
            return

        # Create application
        created_app = await create_application(session, db_user, app_type_enum, data)
        app_id = created_app.id

    await state.clear()
    await callback.answer("Анкета отправлена!")

    # Confirm to user
    is_admin = settings.is_admin(callback.from_user.id)
    await callback.message.answer(
        "✅ <b>Ваша анкета успешно отправлена!</b>\n\n"
        "Администраторы сообщества получили заявку и рассмотрят её в ближайшее время. "
        "Вы получите уведомление о решении здесь, в этом чате.",
        reply_markup=get_main_menu_keyboard(is_admin=is_admin),
        parse_mode="HTML"
    )

    # Deliver card to administrators
    async with get_session() as session:
        fresh_app = await session.get(type(created_app), app_id)
        admin_card_text = format_admin_application(fresh_app)

    admin_keyboard = get_admin_application_keyboard(app_id, ApplicationStatus.NEW)

    # Dispatch to ADMIN_CHAT_ID or list of ADMIN_IDS
    delivered = 0
    recipients = list(settings.admin_ids)
    if settings.ADMIN_CHAT_ID and settings.ADMIN_CHAT_ID not in recipients:
        recipients.append(settings.ADMIN_CHAT_ID)

    for target_id in recipients:
        try:
            sent = await bot.send_message(
                chat_id=target_id,
                text=admin_card_text,
                reply_markup=admin_keyboard,
                parse_mode="HTML"
            )
            delivered += 1
            # Update admin message id
            async with get_session() as session:
                target_app = await session.get(type(created_app), app_id)
                if target_app and not target_app.admin_telegram_message_id:
                    target_app.admin_telegram_message_id = sent.message_id
                    target_app.admin_chat_id = sent.chat.id
        except Exception as e:
            logger.error(f"Failed to deliver application #{app_id} card to admin {target_id}: {e}")

    logger.info(f"Application #{app_id} sent to {delivered} admins.")
