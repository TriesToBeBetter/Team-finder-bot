import re
from typing import Tuple


def validate_text_length(text: str, min_len: int = 2, max_len: int = 1000) -> Tuple[bool, str]:
    """Validate that text is within sensible length boundaries."""
    cleaned = (text or "").strip()
    if len(cleaned) < min_len:
        return False, f"Текст слишком короткий (минимум {min_len} символов). Пожалуйста, опишите подробнее:"
    if len(cleaned) > max_len:
        return False, f"Текст слишком длинный (максимум {max_len} символов). Сократите сообщение:"
    return True, cleaned


def validate_telegram_username(username: str | None) -> str | None:
    """Normalize and validate Telegram username format."""
    if not username:
        return None
    cleaned = username.strip()
    if cleaned.startswith("@"):
        cleaned = cleaned[1:]
    if re.match(r"^[a-zA-Z0-9_]{4,32}$", cleaned):
        return f"@{cleaned}"
    return None
