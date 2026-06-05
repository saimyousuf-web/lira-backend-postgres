from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from core.db import Base


class Conversation(Base):
    __tablename__ = "conversation"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    uid = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    ndid = Column(
        UUID(as_uuid=True),
        ForeignKey("nodes.id"),
        nullable=False,
    )

    cid = Column(
        UUID(as_uuid=True),
        ForeignKey("courses.id"),
        nullable=False,
    )

    title = Column(
        String,
        nullable=True,
    )

    sts = Column(
        String,
        nullable=False,
        default="ACTIVE",
    )

    msgnum = Column(
        Integer,
        nullable=False,
        default=0,
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

    crtby = Column(
        UUID(as_uuid=True),
        nullable=True,
    )

    updby = Column(
        UUID(as_uuid=True),
        nullable=True,
    )