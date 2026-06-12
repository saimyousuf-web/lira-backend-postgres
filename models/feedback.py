from sqlalchemy.orm import Mapped, mapped_column

from core.db import Base
from sqlalchemy import Column, String, Text, DateTime, Boolean, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from models.enums.feedback_status import FeedbackStatus
from sqlalchemy import (
    Column,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from core.db import Base


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default="gen_random_uuid()",
    )

    uid = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    cid = Column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
    )

    convid = Column(
        UUID(as_uuid=True),
        ForeignKey("conversation.id", ondelete="CASCADE"),
        nullable=False,
    )

    sessid = Column(
        UUID(as_uuid=True),
        ForeignKey("session.id", ondelete="CASCADE"),
        nullable=False,
    )

    ndid = Column(
        UUID(as_uuid=True),
        ForeignKey("nodes.id", ondelete="CASCADE"),
        nullable=False,
    )

    # cnm = Column(String(255), nullable=False)

    sessquery = Column(Text, nullable=False)

    # sessmsg = Column(Text, nullable=False)

    feedtxt = Column(Text)

    feedty = Column(String(50), nullable=False)

    rsn = Column(String(255))

    smeres = Column(Text)

    isact = Column(
        Boolean,
        nullable=False,
        server_default="true",
    )

    sts = Column(
        String,
        nullable=False,
        server_default="Pending",
    )

    crtby = Column(UUID(as_uuid=True))

    updby = Column(UUID(as_uuid=True))

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

    __table_args__ = (
        Index("idx_feedback_uid", "uid"),
        Index("idx_feedback_cid", "cid"),
        Index("idx_feedback_convid", "convid"),
        Index("idx_feedback_ndid", "ndid"),
    )
