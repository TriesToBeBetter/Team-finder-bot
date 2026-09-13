import logging
from typing import Dict, Optional
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models import User, Application, ApplicationStatus, AuditLog

logger = logging.getLogger(__name__)


async def get_or_create_user(
    session: AsyncSession,
    telegram_user_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
) -> User:
    """Retrieve existing user or register a new one."""
    stmt = select(User).where(User.telegram_user_id == telegram_user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if user:
        # Update username/first_name if changed
        changed = False
        if username and user.username != username:
            user.username = username
            changed = True
        if first_name and user.first_name != first_name:
            user.first_name = first_name
            changed = True
        if changed:
            user.updated_at = datetime.now(timezone.utc)
            await session.flush()
        return user

    # Create new user
    user = User(
        telegram_user_id=telegram_user_id,
        username=username,
        first_name=first_name,
        is_blocked=False,
    )
    session.add(user)
    await session.flush()
    logger.info(f"New user registered: tg_id={telegram_user_id} @{username}")
    return user


async def is_user_blocked(session: AsyncSession, telegram_user_id: int) -> bool:
    """Check if the user is currently blocked from using the bot."""
    stmt = select(User.is_blocked).where(User.telegram_user_id == telegram_user_id)
    result = await session.execute(stmt)
    is_blocked = result.scalar_one_or_none()
    return bool(is_blocked)


async def set_user_block_status(
    session: AsyncSession,
    telegram_user_id: int,
    blocked: bool,
    admin_id: int,
) -> Optional[User]:
    """Block or unblock a user and record an audit log."""
    stmt = select(User).where(User.telegram_user_id == telegram_user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        return None

    user.is_blocked = blocked
    user.updated_at = datetime.now(timezone.utc)

    # Log audit
    action_name = "block" if blocked else "unblock"
    audit = AuditLog(
        actor_id=admin_id,
        action=action_name,
        details=f"User {telegram_user_id} blocked={blocked} by admin {admin_id}",
    )
    session.add(audit)
    await session.flush()
    logger.warning(f"Admin {admin_id} set user {telegram_user_id} is_blocked={blocked}")
    return user


async def get_platform_stats(session: AsyncSession) -> Dict[str, int]:
    """Retrieve aggregate statistics for the admin dashboard."""
    # Total users
    users_stmt = select(func.count(User.id))
    total_users = (await session.execute(users_stmt)).scalar_one() or 0

    # Blocked users
    blocked_stmt = select(func.count(User.id)).where(User.is_blocked.is_(True))
    blocked_users = (await session.execute(blocked_stmt)).scalar_one() or 0

    # Total applications
    apps_stmt = select(func.count(Application.id))
    total_apps = (await session.execute(apps_stmt)).scalar_one() or 0

    # New applications
    new_stmt = select(func.count(Application.id)).where(Application.status == ApplicationStatus.NEW)
    new_apps = (await session.execute(new_stmt)).scalar_one() or 0

    # Accepted applications
    acc_stmt = select(func.count(Application.id)).where(Application.status == ApplicationStatus.ACCEPTED)
    accepted_apps = (await session.execute(acc_stmt)).scalar_one() or 0

    # Rejected applications
    rej_stmt = select(func.count(Application.id)).where(Application.status == ApplicationStatus.REJECTED)
    rejected_apps = (await session.execute(rej_stmt)).scalar_one() or 0

    return {
        "total_users": total_users,
        "blocked_users": blocked_users,
        "total_apps": total_apps,
        "new_apps": new_apps,
        "accepted_apps": accepted_apps,
        "rejected_apps": rejected_apps,
    }
