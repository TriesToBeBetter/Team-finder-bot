import logging
from typing import List, Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models import AdminMessage, Application

logger = logging.getLogger(__name__)


async def record_chat_message(
    session: AsyncSession,
    application_id: int,
    sender_type: str,
    sender_id: int,
    recipient_id: int,
    text: str,
    telegram_message_id: Optional[int] = None,
) -> AdminMessage:
    """Store an exchanged relay message in the database."""
    msg = AdminMessage(
        application_id=application_id,
        telegram_message_id=telegram_message_id,
        sender_type=sender_type,
        sender_id=sender_id,
        recipient_id=recipient_id,
        text=text,
    )
    session.add(msg)
    await session.flush()
    logger.info(f"Relay message saved: app_id={application_id} {sender_type} ({sender_id}) -> ({recipient_id})")
    return msg


async def get_chat_history(
    session: AsyncSession,
    application_id: int,
    limit: int = 50,
) -> List[AdminMessage]:
    """Retrieve message history between admin and user for a specific application."""
    stmt = (
        select(AdminMessage)
        .where(AdminMessage.application_id == application_id)
        .order_by(AdminMessage.created_at.asc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())
