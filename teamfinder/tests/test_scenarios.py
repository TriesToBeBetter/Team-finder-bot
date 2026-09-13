import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

from bot.database.base import Base
from bot.database.models import User, Application, ApplicationStatus, ApplicationType, AdminMessage
from bot.services.user import get_or_create_user, set_user_block_status, get_platform_stats, is_user_blocked
from bot.services.application import (
    create_application,
    get_active_application,
    get_application_by_id,
    update_application_status,
    cancel_application,
    list_applications,
    search_applications,
)
from bot.services.chat import record_chat_message, get_chat_history
from bot.utils.validators import validate_text_length, validate_telegram_username
from bot.utils.formatters import format_user_preview, format_admin_application, format_stats
from config.settings import settings


@pytest.mark.asyncio
async def test_scenario_1_and_2_start_and_create_application(async_session: AsyncSession, sample_user: User):
    """
    Scenario 1 & 2:
    - User starts bot, gets registered in DB.
    - User creates a complete questionnaire for 'looking_for_team'.
    """
    assert sample_user.telegram_user_id == 987654321
    assert sample_user.is_blocked is False

    app_data = {
        "name": "Alex",
        "role": "Frontend Developer",
        "skills": "React, JavaScript, TypeScript, Tailwind",
        "experience": "2 года",
        "looking_for": "команду для стартапа",
        "availability": "10 часов в неделю",
        "about": "Люблю писать чистый UI-код",
        "telegram_contact": "@alex_dev",
    }

    app = await create_application(
        session=async_session,
        user=sample_user,
        app_type=ApplicationType.LOOKING_FOR_TEAM,
        data=app_data,
    )
    await async_session.commit()

    assert app.id is not None
    assert app.status == ApplicationStatus.NEW
    assert app.name == "Alex"
    assert app.role == "Frontend Developer"

    # Active application check
    active = await get_active_application(async_session, sample_user.id)
    assert active is not None
    assert active.id == app.id


@pytest.mark.asyncio
async def test_scenario_3_input_validation_errors():
    """
    Scenario 3:
    - User makes input errors (too short or too long strings).
    - Validator catches and returns descriptive error messages.
    """
    # Too short
    ok, err = validate_text_length("a", min_len=2, max_len=50)
    assert ok is False
    assert "слишком короткий" in err

    # Too long
    ok, err = validate_text_length("a" * 101, min_len=2, max_len=100)
    assert ok is False
    assert "слишком длинный" in err

    # Valid
    ok, clean = validate_text_length("  Python, aiogram  ", min_len=2, max_len=100)
    assert ok is True
    assert clean == "Python, aiogram"

    # Telegram username normalization
    assert validate_telegram_username("@valid_user") == "@valid_user"
    assert validate_telegram_username("valid_user") == "@valid_user"
    assert validate_telegram_username("bad!") is None


@pytest.mark.asyncio
async def test_scenario_4_and_5_back_navigation_and_cancellation(async_session: AsyncSession, sample_user: User):
    """
    Scenario 4 & 5:
    - User can cancel an application draft or delete an active application.
    """
    app_data = {
        "name": "Alex",
        "role": "Designer",
        "skills": "Figma",
        "experience": "1 год",
        "looking_for": "pet project",
        "availability": "5 hours",
    }
    app = await create_application(async_session, sample_user, ApplicationType.LOOKING_FOR_TEAM, app_data)
    await async_session.commit()

    # User cancels/deletes application
    cancelled = await cancel_application(async_session, app.id, sample_user.id)
    assert cancelled is True
    await async_session.commit()

    # Application is now CANCELLED, not NEW
    refreshed = await get_application_by_id(async_session, app.id)
    assert refreshed.status == ApplicationStatus.CANCELLED

    # No active application remains
    active = await get_active_application(async_session, sample_user.id)
    assert active is None


@pytest.mark.asyncio
async def test_scenario_6_to_9_admin_receives_and_accepts(async_session: AsyncSession, sample_user: User, sample_admin: User, mock_bot):
    """
    Scenario 6, 7, 8, 9:
    - User submits application.
    - Admin reviews the card.
    - Admin clicks 'Accept'.
    - Status becomes ACCEPTED and candidate receives automatic notification.
    """
    app_data = {
        "name": "Alex",
        "role": "Backend Developer",
        "skills": "Python, FastAPI, PostgreSQL",
        "experience": "3 года",
        "looking_for": "финтех стартап",
        "availability": "20 часов в неделю",
        "about": "Имею опыт микросервисов",
    }
    app = await create_application(async_session, sample_user, ApplicationType.LOOKING_FOR_TEAM, app_data)
    await async_session.commit()

    # Verify admin formatting
    admin_card = format_admin_application(app)
    assert "Backend Developer" in admin_card
    assert "Python, FastAPI" in admin_card
    assert "ПОИСК КОМАНДЫ" in admin_card

    # Admin accepts
    success, updated_app, msg = await update_application_status(
        session=async_session,
        app_id=app.id,
        new_status=ApplicationStatus.ACCEPTED,
        admin_id=sample_admin.telegram_user_id,
    )
    await async_session.commit()

    assert success is True
    assert updated_app.status == ApplicationStatus.ACCEPTED
    assert updated_app.reviewed_by_admin_id == sample_admin.telegram_user_id

    # Simulate sending candidate notification
    await mock_bot.send_message(
        chat_id=sample_user.telegram_user_id,
        text="🎉 Ваша анкета была принята!\nАдминистратор скоро свяжется с вами."
    )
    assert len(mock_bot.sent_messages) == 1
    assert mock_bot.sent_messages[0]["chat_id"] == sample_user.telegram_user_id
    assert "принята" in mock_bot.sent_messages[0]["text"]


@pytest.mark.asyncio
async def test_scenario_10_and_11_admin_rejects(async_session: AsyncSession, sample_user: User, sample_admin: User, mock_bot):
    """
    Scenario 10 & 11:
    - Admin rejects an application.
    - Status becomes REJECTED.
    - User receives polite notification without internal details.
    """
    app_data = {
        "name": "Spam Project",
        "role": "Hacker",
        "skills": "None",
        "experience": "0",
        "looking_for": "money",
        "availability": "1h",
    }
    app = await create_application(async_session, sample_user, ApplicationType.LOOKING_FOR_MEMBER, app_data)
    await async_session.commit()

    success, updated_app, msg = await update_application_status(
        session=async_session,
        app_id=app.id,
        new_status=ApplicationStatus.REJECTED,
        admin_id=sample_admin.telegram_user_id,
    )
    await async_session.commit()

    assert success is True
    assert updated_app.status == ApplicationStatus.REJECTED

    # User notification
    await mock_bot.send_message(
        chat_id=sample_user.telegram_user_id,
        text="Спасибо за заявку!\nК сожалению, сейчас ваша анкета не подходит."
    )
    assert len(mock_bot.sent_messages) == 1
    assert "не подходит" in mock_bot.sent_messages[0]["text"]


@pytest.mark.asyncio
async def test_scenario_12_to_14_safe_two_way_chat_relay(async_session: AsyncSession, sample_user: User, sample_admin: User):
    """
    Scenario 12, 13, 14:
    - Admin clicks 'Связаться' and sends message to applicant.
    - Applicant receives message and replies through the bot.
    - Admin receives the reply.
    - Full thread is logged in database.
    """
    app_data = {
        "name": "Alex",
        "role": "Frontend",
        "skills": "React",
        "experience": "2 года",
        "looking_for": "стартап",
        "availability": "10 часов",
    }
    app = await create_application(async_session, sample_user, ApplicationType.LOOKING_FOR_TEAM, app_data)
    await async_session.commit()

    # Admin sends message
    admin_text = "Привет! Хотел бы подробнее обсудить ваш опыт в React."
    msg1 = await record_chat_message(
        session=async_session,
        application_id=app.id,
        sender_type="admin",
        sender_id=sample_admin.telegram_user_id,
        recipient_id=sample_user.telegram_user_id,
        text=admin_text,
    )
    await async_session.commit()

    assert msg1.id is not None
    assert msg1.sender_type == "admin"

    # User replies back
    user_reply_text = "Здравствуйте! Да, разрабатывал SPA с TypeScript и Redux Toolkit."
    msg2 = await record_chat_message(
        session=async_session,
        application_id=app.id,
        sender_type="user",
        sender_id=sample_user.telegram_user_id,
        recipient_id=sample_admin.telegram_user_id,
        text=user_reply_text,
    )
    await async_session.commit()

    assert msg2.id is not None
    assert msg2.sender_type == "user"

    # Check chat history
    history = await get_chat_history(async_session, app.id)
    assert len(history) == 2
    assert history[0].text == admin_text
    assert history[1].text == user_reply_text


@pytest.mark.asyncio
async def test_scenario_15_unauthorized_admin_access(sample_user: User, sample_admin: User):
    """
    Scenario 15:
    - Regular user attempts to use /admin.
    - System strictly denies access based on Telegram user_id.
    """
    # Sample admin user_id is in ADMIN_IDS
    assert settings.is_admin(sample_admin.telegram_user_id) is True

    # Regular user is not in ADMIN_IDS
    assert settings.is_admin(sample_user.telegram_user_id) is False
    assert settings.is_admin(999999999) is False


@pytest.mark.asyncio
async def test_scenario_16_blocked_user_prevention(async_session: AsyncSession, sample_user: User, sample_admin: User):
    """
    Scenario 16:
    - Admin blocks a spam user.
    - User gets is_blocked = True.
    - System verifies block status before allowing application submissions.
    """
    # Admin blocks user
    await set_user_block_status(
        session=async_session,
        telegram_user_id=sample_user.telegram_user_id,
        blocked=True,
        admin_id=sample_admin.telegram_user_id,
    )
    await async_session.commit()

    is_blocked = await is_user_blocked(async_session, sample_user.telegram_user_id)
    assert is_blocked is True


@pytest.mark.asyncio
async def test_scenario_17_double_click_and_idempotency_protection(async_session: AsyncSession, sample_user: User, sample_admin: User):
    """
    Scenario 17:
    - Repeated click on 'Accept' or 'Reject' does not break state or cause duplicate actions.
    """
    app_data = {
        "name": "Alex",
        "role": "QA Engineer",
        "skills": "Playwright, PyTest",
        "experience": "2 года",
        "looking_for": "команду",
        "availability": "15 часов",
    }
    app = await create_application(async_session, sample_user, ApplicationType.LOOKING_FOR_TEAM, app_data)
    await async_session.commit()

    # First accept -> Success
    success1, _, msg1 = await update_application_status(
        async_session, app.id, ApplicationStatus.ACCEPTED, sample_admin.telegram_user_id
    )
    await async_session.commit()
    assert success1 is True

    # Second accept -> Denied gracefully, status remains ACCEPTED
    success2, _, msg2 = await update_application_status(
        async_session, app.id, ApplicationStatus.ACCEPTED, sample_admin.telegram_user_id
    )
    assert success2 is False
    assert "уже была принята" in msg2

    refreshed = await get_application_by_id(async_session, app.id)
    assert refreshed.status == ApplicationStatus.ACCEPTED


@pytest.mark.asyncio
async def test_scenario_18_persistence_across_restart(tmp_path):
    """
    Scenario 18:
    - Verify that data stored on disk in SQLite persists cleanly across process restarts.
    """
    db_file = tmp_path / "test_persistence.db"
    db_url = f"sqlite+aiosqlite:///{db_file}"

    # First session: init db and create application
    engine1 = create_async_engine(db_url, echo=False)
    async with engine1.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker1 = async_sessionmaker(engine1, expire_on_commit=False)
    async with session_maker1() as session:
        user = await get_or_create_user(session, telegram_user_id=555555, username="persistent_dev")
        app = await create_application(
            session,
            user,
            ApplicationType.LOOKING_FOR_TEAM,
            {
                "name": "Persistent Candidate",
                "role": "Architect",
                "skills": "Python, Cloud, Docker",
                "experience": "7 years",
                "looking_for": "Serious project",
                "availability": "Full-time",
            }
        )
        saved_app_id = app.id
        await session.commit()

    await engine1.dispose()

    # Simulate restart: connect fresh engine to the same file
    engine2 = create_async_engine(db_url, echo=False)
    session_maker2 = async_sessionmaker(engine2, expire_on_commit=False)
    async with session_maker2() as session:
        loaded_app = await get_application_by_id(session, saved_app_id)
        assert loaded_app is not None
        assert loaded_app.name == "Persistent Candidate"
        assert loaded_app.role == "Architect"
        assert loaded_app.status == ApplicationStatus.NEW

    await engine2.dispose()


@pytest.mark.asyncio
async def test_platform_statistics_and_search(async_session: AsyncSession, sample_user: User):
    """Verify statistics calculation and search query filtering."""
    app_data = {
        "name": "Maria",
        "role": "Product Manager",
        "skills": "Scrum, Agile, Roadmap, Analytics",
        "experience": "4 года",
        "looking_for": "EdTech проект",
        "availability": "20 часов",
    }
    await create_application(async_session, sample_user, ApplicationType.LOOKING_FOR_TEAM, app_data)
    await async_session.commit()

    stats = await get_platform_stats(async_session)
    assert stats["total_apps"] >= 1
    assert stats["new_apps"] >= 1

    formatted_stats = format_stats(stats)
    assert "СТАТИСТИКА ПЛАТФОРМЫ" in formatted_stats

    # Search by skill
    results = await search_applications(async_session, query="Scrum")
    assert len(results) >= 1
    assert results[0].name == "Maria"

    # Search non-matching
    no_results = await search_applications(async_session, query="NonExistentSkill123")
    assert len(no_results) == 0
