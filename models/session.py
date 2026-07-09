from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.db import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.conversation import Conversation

class Session(Base):
    __tablename__ = "session"

    __table_args__ = (
        CheckConstraint(
            "sender IN ('USER', 'BOT')",
            name="session_sender_check",
        ),
        Index(
            "idx_chats_session",
            "convid",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    convid: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("conversation.id", ondelete="CASCADE"),
        nullable=False,
    )

    msgtxt: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    sender: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    crtby: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
    )

    updby: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
    )

    crtat: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updat: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    conversation: Mapped["Conversation"] = relationship(
        back_populates="sessions",
    )