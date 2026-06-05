import uuid

from sqlalchemy import (
    Column,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from core.db import Base


class Module(Base):
    __tablename__ = "module"

    __table_args__ = (
        Index("idx_modules_status", "sts"),
        Index("idx_modules_vectorized", "isvec"),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    nm = Column(
        String(255),
        nullable=False,
    )

    ty = Column(
        String(50),
        nullable=True,
    )

    loc = Column(
        Text,
        nullable=True,
    )

    isapr = Column(
        Boolean,
        nullable=False,
        server_default="false",
    )

    sts = Column(
        String(50),
        nullable=False,
        server_default="DRAFT",
    )

    isvec = Column(
        Boolean,
        nullable=False,
        server_default="false",
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


