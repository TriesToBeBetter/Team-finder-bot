from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_menu_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Main persistent reply keyboard for user navigation."""
    buttons = [
        [KeyboardButton(text="🔎 Найти команду"), KeyboardButton(text="👥 Найти участника")],
        [KeyboardButton(text="📋 Моя анкета"), KeyboardButton(text="❓ Помощь")],
    ]
    if is_admin:
        buttons.append([KeyboardButton(text="🛡 Админ-панель (/admin)")])

    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        is_persistent=True,
    )


def get_step_navigation_keyboard() -> ReplyKeyboardMarkup:
    """Navigation keyboard displayed during questionnaire steps with Back and Cancel."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⬅️ Назад"), KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Simple cancel keyboard for single-step input."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True,
    )
