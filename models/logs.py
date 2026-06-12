import uuid

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from core.db import Base


class Log(Base):
    __tablename__ = "logs"

    __table_args__ = (
        Index("idx_logs_cid",      "cid"),
        Index("idx_logs_old_moid", "oldmoid"),
        Index("idx_logs_new_moid", "newmoid"),
        Index("idx_logs_updat",    "updat"),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    cid = Column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
    )

    oldmoid = Column(
        UUID(as_uuid=True),
        ForeignKey("module.id", ondelete="SET NULL"),
        nullable=True,
    )

    newmoid = Column(
        UUID(as_uuid=True),
        ForeignKey("module.id", ondelete="SET NULL"),
        nullable=True,
    )

    updat = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updby = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )