import html
from typing import Dict, Any
from bot.database.models import Application, ApplicationStatus, ApplicationType


def escape(text: Any) -> str:
    """Safely escape HTML entities for Telegram HTML formatting mode."""
    if text is None:
        return ""
    return html.escape(str(text))


def format_user_preview(data: Dict[str, Any], app_type: ApplicationType) -> str:
    """Format questionnaire data for user confirmation prior to submission."""
    if app_type == ApplicationType.LOOKING_FOR_TEAM:
        header = "<b>📋 Проверьте вашу анкету (Поиск команды):</b>\n"
        body = (
            f"👤 <b>Имя / Никнейм:</b> {escape(data.get('name'))}\n"
            f"🎯 <b>Роль:</b> {escape(data.get('role'))}\n"
            f"💻 <b>Навыки:</b> {escape(data.get('skills'))}\n"
            f"📈 <b>Опыт:</b> {escape(data.get('experience'))}\n"
            f"🔎 <b>Ищу:</b> {escape(data.get('looking_for'))}\n"
            f"⏰ <b>Время / Занятость:</b> {escape(data.get('availability'))}\n"
            f"📝 <b>О себе:</b> {escape(data.get('about') or 'Не указано')}\n"
            f"🔗 <b>Контакт:</b> {escape(data.get('telegram_contact') or 'Текущий аккаунт')}"
        )
    else:
        header = "<b>📋 Проверьте заявку проекта (Поиск участника):</b>\n"
        body = (
            f"🚀 <b>Проект / Контактное лицо:</b> {escape(data.get('name'))}\n"
            f"🎯 <b>Кого ищете:</b> {escape(data.get('role'))}\n"
            f"💻 <b>Требуемые навыки:</b> {escape(data.get('skills'))}\n"
            f"📈 <b>Требуемый опыт:</b> {escape(data.get('experience'))}\n"
            f"📖 <b>О проекте:</b> {escape(data.get('project_description') or data.get('looking_for'))}\n"
            f"⏰ <b>Занятость:</b> {escape(data.get('availability'))}\n"
            f"📝 <b>Дополнительно:</b> {escape(data.get('about') or 'Не указано')}\n"
            f"🔗 <b>Контакт:</b> {escape(data.get('telegram_contact') or 'Текущий аккаунт')}"
        )

    return f"{header}\n{body}\n\n<b>Всё верно?</b>"


def format_admin_application(app: Application) -> str:
    """Format full application card for the administrator review panel."""
    is_team_search = (app.type == ApplicationType.LOOKING_FOR_TEAM)
    
    type_title = "🔎 ПОИСК КОМАНДЫ (СПЕЦИАЛИСТ)" if is_team_search else "👥 ПОИСК УЧАСТНИКА В ПРОЕКТ"
    badge = f"#{app.id} • {type_title}"

    status_badge = {
        ApplicationStatus.NEW: "🟡 НОВАЯ АНКЕТА",
        ApplicationStatus.ACCEPTED: "🟢 ПРИНЯТО",
        ApplicationStatus.REJECTED: "🔴 ОТКЛОНЕНО",
        ApplicationStatus.CANCELLED: "⚪️ ОТОЗВАНА",
    }.get(app.status, str(app.status))

    contact_info = escape(app.telegram_contact or (f"@{app.user.username}" if app.user and app.user.username else f"ID: {app.user.telegram_user_id if app.user else 'Н/Д'}"))

    if is_team_search:
        card = (
            f"━━━━━━━━━━━━━━\n"
            f"<b>{badge}</b>\n"
            f"Статус: <b>{status_badge}</b>\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"👤 <b>{escape(app.name)}</b> (Контакт: {contact_info})\n\n"
            f"🎯 <b>Роль:</b>\n{escape(app.role)}\n\n"
            f"💻 <b>Навыки:</b>\n{escape(app.skills)}\n\n"
            f"📈 <b>Опыт:</b>\n{escape(app.experience)}\n\n"
            f"🔎 <b>Ищет:</b>\n{escape(app.looking_for)}\n\n"
            f"⏰ <b>Время:</b>\n{escape(app.availability)}\n\n"
            f"📝 <b>О себе:</b>\n{escape(app.about or 'Не указано')}\n\n"
            f"📅 Дата: {app.created_at.strftime('%d.%m.%Y %H:%M') if app.created_at else ''}\n"
            f"━━━━━━━━━━━━━━"
        )
    else:
        card = (
            f"━━━━━━━━━━━━━━\n"
            f"<b>{badge}</b>\n"
            f"Статус: <b>{status_badge}</b>\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"🚀 <b>Проект: {escape(app.name)}</b> (Контакт: {contact_info})\n\n"
            f"🎯 <b>Ищет специалиста:</b>\n{escape(app.role)}\n\n"
            f"💻 <b>Требуемые навыки:</b>\n{escape(app.skills)}\n\n"
            f"📈 <b>Опыт:</b>\n{escape(app.experience)}\n\n"
            f"📖 <b>О проекте:</b>\n{escape(app.project_description or app.looking_for)}\n\n"
            f"⏰ <b>Занятость:</b>\n{escape(app.availability)}\n\n"
            f"📝 <b>Дополнительно:</b>\n{escape(app.about or 'Не указано')}\n\n"
            f"📅 Дата: {app.created_at.strftime('%d.%m.%Y %H:%M') if app.created_at else ''}\n"
            f"━━━━━━━━━━━━━━"
        )
    return card


def format_user_profile(app: Application) -> str:
    """Format single user's existing application for the 'Моя анкета' view."""
    status_icon = {
        ApplicationStatus.NEW: "🟡 На рассмотрении у модераторов",
        ApplicationStatus.ACCEPTED: "🟢 Принята! Скоро с вами свяжутся",
        ApplicationStatus.REJECTED: "🔴 Не подошла",
        ApplicationStatus.CANCELLED: "⚪️ Отозвана",
    }.get(app.status, str(app.status))

    is_team_search = (app.type == ApplicationType.LOOKING_FOR_TEAM)
    role_label = "Ваша роль" if is_team_search else "Ищете"

    return (
        f"<b>📋 Ваша анкета #{app.id}</b>\n\n"
        f"Статус: <b>{status_icon}</b>\n\n"
        f"👤 <b>Имя/Проект:</b> {escape(app.name)}\n"
        f"🎯 <b>{role_label}:</b> {escape(app.role)}\n"
        f"💻 <b>Навыки:</b> {escape(app.skills)}\n"
        f"📈 <b>Опыт:</b> {escape(app.experience)}\n"
        f"🔎 <b>Цель / О проекте:</b> {escape(app.project_description or app.looking_for)}\n"
        f"⏰ <b>Занятость:</b> {escape(app.availability)}\n"
        f"📝 <b>О себе:</b> {escape(app.about or 'Не указано')}\n"
        f"📅 Создана: {app.created_at.strftime('%d.%m.%Y %H:%M') if app.created_at else ''}"
    )


def format_stats(stats: Dict[str, int]) -> str:
    """Format statistical dashboard numbers for /admin."""
    return (
        f"<b>📊 СТАТИСТИКА ПЛАТФОРМЫ TEAMFINDER</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👥 Всего пользователей: <b>{stats.get('total_users', 0)}</b>\n"
        f"📑 Всего анкет/заявок: <b>{stats.get('total_apps', 0)}</b>\n\n"
        f"📥 Новых (на рассмотрении): <b>{stats.get('new_apps', 0)}</b>\n"
        f"✅ Принятых: <b>{stats.get('accepted_apps', 0)}</b>\n"
        f"❌ Отклонённых: <b>{stats.get('rejected_apps', 0)}</b>\n"
        f"🚫 Заблокированных пользователей: <b>{stats.get('blocked_users', 0)}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━"
    )
