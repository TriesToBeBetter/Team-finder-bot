import pytest
import pytest_asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from bot.database.base import Base
from bot.database.models import User, Application, ApplicationStatus, ApplicationType
from bot.services.user import get_or_create_user
from config.settings import settings


@pytest_asyncio.fixture
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an isolated, transactional in-memory SQLite async database session for testing."""
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        yield session

    await test_engine.dispose()


@pytest_asyncio.fixture
async def sample_admin(async_session: AsyncSession) -> User:
    """Create a sample administrator user."""
    admin = await get_or_create_user(
        session=async_session,
        telegram_user_id=123456789,
        username="lead_admin",
        first_name="Admin",
    )
    await async_session.commit()
    return admin


@pytest_asyncio.fixture
async def sample_user(async_session: AsyncSession) -> User:
    """Create a regular applicant user."""
    user = await get_or_create_user(
        session=async_session,
        telegram_user_id=987654321,
        username="alex_dev",
        first_name="Alex",
    )
    await async_session.commit()
    return user


class MockBotMessageStore:
    """In-memory mock store for sent telegram bot messages during tests."""
    def __init__(self):
        self.sent_messages = []

    async def send_message(self, chat_id: int, text: str, **kwargs):
        msg = {
            "chat_id": chat_id,
            "text": text,
            "kwargs": kwargs,
        }
        self.sent_messages.append(msg)
        return msg


@pytest.fixture
def mock_bot() -> MockBotMessageStore:
    return MockBotMessageStore()
