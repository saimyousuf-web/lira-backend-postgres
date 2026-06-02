import uuid
from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from core.db import Base


class NodeType(Base):
    __tablename__ = "node_types"

    id   = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ty = Column(String(10), nullable=False, unique=True)


class Node(Base):
    __tablename__ = "nodes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ndtyid = Column(UUID(as_uuid=True), ForeignKey("node_types.id"), nullable=False)

    ndty = relationship("NodeType")


class Org(Base):
    __tablename__ = "orgs"
    __table_args__ = (
        UniqueConstraint("nm", name="uq_org_name"),
    )

    ndid      = Column(UUID(as_uuid=True), ForeignKey("nodes.id", ondelete="CASCADE"), primary_key=True)
    orgid       = Column(UUID(as_uuid=True), ForeignKey("orgs.node_id"), nullable=False)  # self-ref
    prtndid    = Column(UUID(as_uuid=True), nullable=True, default=None)
    nm         = Column(String(255), nullable=False)
    title        = Column(String(255))
    favicon_path = Column(String, nullable=True)
    logo_path    = Column(String, nullable=True)
    isact    = Column(Boolean, nullable=False, default=True)
    crtby   = Column(UUID(as_uuid=True))
    updby   = Column(UUID(as_uuid=True))
    crtat   = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updat   = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Dept(Base):
    __tablename__ = "depts"
    __table_args__ = (
        UniqueConstraint("prtndid", "nm", name="uq_dept_name_per_parent"),
    )

    ndid    = Column(UUID(as_uuid=True), ForeignKey("nodes.id", ondelete="CASCADE"), primary_key=True)
    orgid     = Column(UUID(as_uuid=True), ForeignKey("orgs.ndid"), nullable=False)
    prtndid  = Column(UUID(as_uuid=True), ForeignKey("nodes.id"), nullable=False)
    nm       = Column(String(255), nullable=False)
    isact  = Column(Boolean, nullable=False, default=True)
    crtby = Column(UUID(as_uuid=True))
    updby = Column(UUID(as_uuid=True))
    crtat = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updat = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Func(Base):
    __tablename__ = "funcs"
    __table_args__ = (
        UniqueConstraint("prtndid", "nm", name="uq_func_name_per_parent"),
    )

    ndid    = Column(UUID(as_uuid=True), ForeignKey("nodes.id", ondelete="CASCADE"), primary_key=True)
    orgid     = Column(UUID(as_uuid=True), ForeignKey("orgs.ndid"), nullable=False)
    prtndid  = Column(UUID(as_uuid=True), ForeignKey("nodes.id"), nullable=False)
    nm       = Column(String(255), nullable=False)
    isact  = Column(Boolean, nullable=False, default=True)
    crtby = Column(UUID(as_uuid=True))
    updby = Column(UUID(as_uuid=True))
    crtat = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updat = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)