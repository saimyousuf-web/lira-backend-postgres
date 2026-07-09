from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base


class NodeType(Base):
    __tablename__ = "node_types"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    ty: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        unique=True,
    )


class Node(Base):
    __tablename__ = "nodes"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    ndtyid: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("node_types.id"),
        nullable=False,
    )

    ndty: Mapped[NodeType] = relationship()


class Org(Base):
    __tablename__ = "orgs"
    __table_args__ = (
        UniqueConstraint("nm", name="uq_org_name"),
    )

    ndid: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("nodes.id", ondelete="CASCADE"),
        primary_key=True,
    )

    orgid: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("orgs.ndid"),
        nullable=False,
    )

    prtndid: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
        default=None,
    )

    nm: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    title: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    favicon_path: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    logo_path: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    isact: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
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
        server_default=func.now(),
        nullable=False,
    )

    updat: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class Dept(Base):
    __tablename__ = "depts"
    __table_args__ = (
        UniqueConstraint("prtndid", "nm", name="uq_dept_name_per_parent"),
    )

    ndid: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("nodes.id", ondelete="CASCADE"),
        primary_key=True,
    )

    orgid: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("orgs.ndid"),
        nullable=False,
    )

    prtndid: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("nodes.id"),
        nullable=False,
    )

    nm: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    isact: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
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
        server_default=func.now(),
        nullable=False,
    )

    updat: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class Func(Base):
    __tablename__ = "funcs"
    __table_args__ = (
        UniqueConstraint("prtndid", "nm", name="uq_func_name_per_parent"),
    )

    ndid: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("nodes.id", ondelete="CASCADE"),
        primary_key=True,
    )

    orgid: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("orgs.ndid"),
        nullable=False,
    )

    prtndid: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("nodes.id"),
        nullable=False,
    )

    nm: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    isact: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
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
        server_default=func.now(),
        nullable=False,
    )

    updat: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )