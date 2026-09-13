from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.database.models import ApplicationStatus


def get_confirm_keyboard() -> InlineKeyboardMarkup:
    """Inline keyboard for final application review before sending."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Отправить", callback_data="app_submit")],
            [
                InlineKeyboardButton(text="✏️ Изменить", callback_data="app_edit"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="app_cancel"),
            ],
        ]
    )


def get_admin_application_keyboard(app_id: int, status: ApplicationStatus = ApplicationStatus.NEW) -> InlineKeyboardMarkup:
    """Interactive control keyboard attached to an application card in the admin chat."""
    if status == ApplicationStatus.NEW:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Принять", callback_data=f"adm_accept:{app_id}"),
                    InlineKeyboardButton(text="❌ Отклонить", callback_data=f"adm_reject:{app_id}"),
                ],
                [
                    InlineKeyboardButton(text="💬 Связаться", callback_data=f"adm_contact:{app_id}"),
                    InlineKeyboardButton(text="🚫 Заблокировать", callback_data=f"adm_block:{app_id}"),
                ],
            ]
        )
    elif status == ApplicationStatus.ACCEPTED:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🟢 ПРИНЯТО", callback_data=f"adm_noop:{app_id}")],
                [InlineKeyboardButton(text="💬 Написать пользователю", callback_data=f"adm_contact:{app_id}")],
            ]
        )
    elif status == ApplicationStatus.REJECTED:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔴 ОТКЛОНЕНО", callback_data=f"adm_noop:{app_id}")],
            ]
        )
    else:  # CANCELLED or other
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⚪️ АНКЕТА ОТОЗВАНА", callback_data=f"adm_noop:{app_id}")],
            ]
        )


def get_admin_panel_keyboard() -> InlineKeyboardMarkup:
    """Main hub inline keyboard for the /admin dashboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📥 Новые заявки", callback_data="adm_list:new"),
                InlineKeyboardButton(text="📊 Статистика", callback_data="adm_stats"),
            ],
            [
                InlineKeyboardButton(text="✅ Принятые", callback_data="adm_list:accepted"),
                InlineKeyboardButton(text="❌ Отклонённые", callback_data="adm_list:rejected"),
            ],
            [
                InlineKeyboardButton(text="🚫 Заблокированные", callback_data="adm_list:blocked"),
                InlineKeyboardButton(text="🔍 Поиск", callback_data="adm_search"),
            ],
            [
                InlineKeyboardButton(text="⚙️ Настройки", callback_data="adm_settings"),
                InlineKeyboardButton(text="🔄 Обновить", callback_data="adm_refresh"),
            ],
        ]
    )


def get_user_reply_keyboard(app_id: int) -> InlineKeyboardMarkup:
    """Button for a user to reply back to an administrator's message."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💬 Ответить администратору", callback_data=f"user_reply:{app_id}")]
        ]
    )


def get_my_profile_keyboard(has_active_application: bool, app_id: int | None = None) -> InlineKeyboardMarkup:
    """Keyboard for 'Моя анкета' view."""
    if has_active_application and app_id:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✏️ Изменить анкету", callback_data=f"prof_edit:{app_id}"),
                    InlineKeyboardButton(text="🗑 Удалить анкету", callback_data=f"prof_delete:{app_id}"),
                ],
                [InlineKeyboardButton(text="⬅️ В главное меню", callback_data="prof_back_main")],
            ]
        )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔎 Найти команду", callback_data="start_team_search")],
            [InlineKeyboardButton(text="👥 Найти участника", callback_data="start_member_search")],
        ]
    )
