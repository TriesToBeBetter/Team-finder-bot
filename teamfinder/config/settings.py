from typing import List, Set
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application configuration loaded from environment variables or .env file."""
    
    BOT_TOKEN: str = Field(default="123456789:ABCDefghIJKlmnoPQRstuvWXyz", description="Telegram Bot Token from @BotFather")
    ADMIN_IDS_RAW: str = Field(default="123456789", alias="ADMIN_IDS", description="Comma-separated Telegram user IDs of administrators")
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///teamfinder.db", description="SQLAlchemy database connection URL (SQLite or PostgreSQL)")
    ADMIN_CHAT_ID: int | None = Field(default=None, description="Optional dedicated Telegram group/channel ID for admin notifications")
    GEMINI_API_KEY: str | None = Field(default=None, description="Optional Google Gemini API key for smart resume structuring")
    LOG_LEVEL: str = Field(default="INFO", description="Logging verbosity (DEBUG, INFO, WARNING, ERROR)")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def admin_ids(self) -> Set[int]:
        """Parsed set of integer admin user IDs for O(1) security lookup."""
        result: Set[int] = set()
        if not self.ADMIN_IDS_RAW:
            return result
        for item in str(self.ADMIN_IDS_RAW).split(","):
            cleaned = item.strip()
            if cleaned.isdigit():
                result.add(int(cleaned))
        return result

    def is_admin(self, user_id: int) -> bool:
        """Securely verify if user_id belongs to authorized administrators."""
        return user_id in self.admin_ids


# Global settings singleton
settings = Settings()
