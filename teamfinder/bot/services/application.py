import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from sqlalchemy import select, or_, desc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import Application, ApplicationStatus, ApplicationType, AuditLog, User

logger = logging.getLogger(__name__)


async def get_active_application(session: AsyncSession, user_id: int) -> Optional[Application]:
    """Retrieve current active application (NEW or ACCEPTED) for a user to avoid spam duplicates."""
    stmt = (
        select(Application)
        .where(
            Application.user_id == user_id,
            Application.status.in_([ApplicationStatus.NEW, ApplicationStatus.ACCEPTED]),
        )
        .order_by(desc(Application.created_at))
        .options(selectinload(Application.user))
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_application_by_id(session: AsyncSession, app_id: int) -> Optional[Application]:
    """Retrieve application by its primary key with user eagerly loaded."""
    stmt = (
        select(Application)
        .where(Application.id == app_id)
        .options(selectinload(Application.user))
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_application(
    session: AsyncSession,
    user: User,
    app_type: ApplicationType,
    data: Dict[str, Any],
) -> Application:
    """Create a new application and save it to the database."""
    app = Application(
        user_id=user.id,
        type=app_type,
        name=str(data.get("name", "")).strip(),
        role=str(data.get("role", "")).strip(),
        skills=str(data.get("skills", "")).strip(),
        experience=str(data.get("experience", "")).strip(),
        looking_for=str(data.get("looking_for", "")).strip(),
        project_description=str(data.get("project_description", "")).strip() if data.get("project_description") else None,
        availability=str(data.get("availability", "")).strip(),
        about=str(data.get("about", "")).strip() if data.get("about") else None,
        telegram_contact=str(data.get("telegram_contact", "")).strip() if data.get("telegram_contact") else (f"@{user.username}" if user.username else None),
        status=ApplicationStatus.NEW,
    )
    session.add(app)
    await session.flush()

    # Log audit record
    audit = AuditLog(
        application_id=app.id,
        actor_id=user.telegram_user_id,
        action="create_application",
        details=f"Created {app_type.value} application #{app.id} for user {user.telegram_user_id}",
    )
    session.add(audit)
    await session.flush()

    logger.info(f"Created application #{app.id} (type={app_type.value}) by user {user.telegram_user_id}")
    return app


async def update_application_status(
    session: AsyncSession,
    app_id: int,
    new_status: ApplicationStatus,
    admin_id: int,
    admin_notes: Optional[str] = None,
) -> tuple[bool, Optional[Application], str]:
    """
    Safely update application status with strict concurrency/idempotency protection.
    Returns: (success: bool, app: Optional[Application], message: str)
    """
    app = await get_application_by_id(session, app_id)
    if not app:
        return False, None, "Анкета не найдена в базе данных."

    # Guard against repeat status application
    if app.status == new_status:
        status_name = "принята" if new_status == ApplicationStatus.ACCEPTED else "отклонена"
        return False, app, f"Эта заявка уже была {status_name} ранее."

    previous_status = app.status
    app.status = new_status
    app.reviewed_by_admin_id = admin_id
    if admin_notes:
        app.admin_notes = admin_notes
    app.updated_at = datetime.now(timezone.utc)

    # Log audit
    audit = AuditLog(
        application_id=app.id,
        actor_id=admin_id,
        action=f"status_to_{new_status.value}",
        details=f"Status changed from {previous_status.value} to {new_status.value} by admin {admin_id}",
    )
    session.add(audit)
    await session.flush()

    logger.info(f"Admin {admin_id} changed application #{app_id} status: {previous_status.value} -> {new_status.value}")
    return True, app, "Статус успешно обновлен."


async def cancel_application(session: AsyncSession, app_id: int, user_id: int) -> bool:
    """Allow user to cancel/delete their own active application."""
    app = await get_application_by_id(session, app_id)
    if not app or app.user_id != user_id:
        return False

    app.status = ApplicationStatus.CANCELLED
    app.updated_at = datetime.now(timezone.utc)

    audit = AuditLog(
        application_id=app.id,
        actor_id=app.user.telegram_user_id,
        action="cancel_application",
        details=f"User cancelled application #{app.id}",
    )
    session.add(audit)
    await session.flush()
    logger.info(f"User {user_id} cancelled application #{app_id}")
    return True


async def list_applications(
    session: AsyncSession,
    status: Optional[ApplicationStatus] = None,
    limit: int = 10,
    offset: int = 0,
) -> List[Application]:
    """Query applications by status with pagination."""
    stmt = select(Application).options(selectinload(Application.user)).order_by(desc(Application.created_at))
    if status is not None:
        stmt = stmt.where(Application.status == status)
    stmt = stmt.limit(limit).offset(offset)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def search_applications(
    session: AsyncSession,
    query: str,
    limit: int = 10,
) -> List[Application]:
    """Search applications across name, role, skills, and search criteria."""
    search_term = f"%{query.strip()}%"
    stmt = (
        select(Application)
        .options(selectinload(Application.user))
        .where(
            or_(
                Application.name.ilike(search_term),
                Application.role.ilike(search_term),
                Application.skills.ilike(search_term),
                Application.looking_for.ilike(search_term),
            )
        )
        .order_by(desc(Application.created_at))
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())
