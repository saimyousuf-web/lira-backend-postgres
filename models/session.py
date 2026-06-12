from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    ForeignKey,
    CheckConstraint,
    Index,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from core.db import Base


class Session(Base):
    __tablename__ = "session"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    convid = Column(
        UUID(as_uuid=True),
        ForeignKey("conversation.id", ondelete="CASCADE"),
        nullable=False,
    )

    msgtxt = Column(
        Text,
        nullable=False,
    )

    sender = Column(
        String(10),
        nullable=False,
    )

    crtby = Column(
        UUID(as_uuid=True),
        nullable=True,
    )

    updby = Column(
        UUID(as_uuid=True),
        nullable=True,
    )

    crtat = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updat = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    conversation = relationship(
        "Conversation",
        back_populates="sessions",
    )

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