import enum
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class ApplicationType(str, enum.Enum):
    LOOKING_FOR_TEAM = "looking_for_team"       # Человек ищет команду (специалист)
    LOOKING_FOR_MEMBER = "looking_for_member"   # Проект/команда ищет участника


class ApplicationStatus(str, enum.Enum):
    NEW = "new"              # Новая анкета
    ACCEPTED = "accepted"    # Принята администратором
    REJECTED = "rejected"    # Отклонена
    CANCELLED = "cancelled"  # Удалена/отозвана автором


class User(Base):
    """User representation in the system."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    applications: Mapped[List["Application"]] = relationship(
        "Application",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="desc(Application.created_at)"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} tg_id={self.telegram_user_id} username=@{self.username} blocked={self.is_blocked}>"


class Application(Base):
    """Application/Resume submitted by a user looking for a team or member."""
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    
    type: Mapped[ApplicationType] = mapped_column(
        SQLEnum(ApplicationType, native_enum=False),
        default=ApplicationType.LOOKING_FOR_TEAM,
        nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(255), nullable=False)
    skills: Mapped[str] = mapped_column(Text, nullable=False)
    experience: Mapped[str] = mapped_column(String(255), nullable=False)
    looking_for: Mapped[str] = mapped_column(Text, nullable=False)
    project_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    availability: Mapped[str] = mapped_column(String(255), nullable=False)
    about: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    telegram_contact: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    status: Mapped[ApplicationStatus] = mapped_column(
        SQLEnum(ApplicationStatus, native_enum=False),
        default=ApplicationStatus.NEW,
        index=True,
        nullable=False
    )
    
    admin_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Telegram message ID where this application card is posted in admin chat or admin private chat
    admin_telegram_message_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    admin_chat_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    reviewed_by_admin_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="applications")
    messages: Mapped[List["AdminMessage"]] = relationship(
        "AdminMessage",
        back_populates="application",
        cascade="all, delete-orphan",
        order_by="asc(AdminMessage.created_at)"
    )

    def __repr__(self) -> str:
        return f"<Application id={self.id} user_id={self.user_id} type={self.type} status={self.status}>"


class AdminMessage(Base):
    """Messages relayed safely between admin and applicant through the bot."""
    __tablename__ = "admin_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    application_id: Mapped[int] = mapped_column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), index=True, nullable=False)
    telegram_message_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    
    sender_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'admin' or 'user'
    sender_id: Mapped[int] = mapped_column(BigInteger, nullable=False)      # Telegram user id of sender
    recipient_id: Mapped[int] = mapped_column(BigInteger, nullable=False)   # Telegram user id of recipient
    text: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    application: Mapped["Application"] = relationship("Application", back_populates="messages")

    def __repr__(self) -> str:
        return f"<AdminMessage id={self.id} app_id={self.application_id} sender={self.sender_type}>"


class AuditLog(Base):
    """Audit log for lifecycle events and state transitions for debugging & admin history."""
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    application_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    actor_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
