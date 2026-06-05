import uuid

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from core.db import Base

class CourseModule(Base):
    __tablename__ = "course_module"

    __table_args__ = (
        Index("idx_cm_module", "moid"),
    )

    cid = Column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )

    moid = Column(
        UUID(as_uuid=True),
        ForeignKey("module.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )

    crtby = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    updby = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
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