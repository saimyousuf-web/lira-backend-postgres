from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from core.db import Base


class Module(Base):
    __tablename__ = "module"

    __table_args__ = (
        Index("idx_modules_status", "sts"),
        Index("idx_modules_vectorized", "isvec"),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    nm: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    ty: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    loc: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    isapr: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
    )

    sts: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        server_default="DRAFT",
    )

    isvec: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
    )

    crtby: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    updby: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
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