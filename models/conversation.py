from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    ForeignKey,
    CheckConstraint,
    Index,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from core.db import Base


class Conversation(Base):
    __tablename__ = "conversation"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )

    uid = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    ndid = Column(
        UUID(as_uuid=True),
        ForeignKey("nodes.id", ondelete="CASCADE"),
        nullable=False,
    )

    cid = Column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
    )

    title = Column(String(255), nullable=True)
    step = Column(String(255), nullable=True)

    sts = Column(
        String(20),
        nullable=False,
        server_default="ACTIVE",
    )

    msgnum = Column(
        Integer,
        nullable=False,
        server_default="0",
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

    crtby = Column(UUID(as_uuid=True), nullable=True)
    updby = Column(UUID(as_uuid=True), nullable=True)

    
    sessions = relationship(
        "Session",
        back_populates="conversation",
    )


    __table_args__ = (
        CheckConstraint(
            "sts IN ('ACTIVE', 'CLOSED')",
            name="conversation_sts_check",
        ),
        Index("idx_sessions_user", "uid"),
        Index("idx_sessions_node", "ndid"),
        Index("idx_sessions_course", "cid"),
    )