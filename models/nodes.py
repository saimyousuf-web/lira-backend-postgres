import uuid
from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from core.db import Base


class NodeType(Base):
    __tablename__ = "node_types"

    id   = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(String(10), nullable=False, unique=True)


class Node(Base):
    __tablename__ = "nodes"

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    node_type_id = Column(UUID(as_uuid=True), ForeignKey("node_types.id"), nullable=False)

    node_type = relationship("NodeType")


class Org(Base):
    __tablename__ = "orgs"

    node_id      = Column(UUID(as_uuid=True), ForeignKey("nodes.id", ondelete="CASCADE"), primary_key=True)
    parent_id    = Column(UUID(as_uuid=True), nullable=True, default=None)
    name         = Column(String(255), nullable=False)
    title        = Column(String(255))
    favicon_path = Column(String)
    logo_path    = Column(String)
    is_active    = Column(Boolean, nullable=False, default=True)
    created_by   = Column(UUID(as_uuid=True))
    updated_by   = Column(UUID(as_uuid=True))
    created_at   = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at   = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Dept(Base):
    __tablename__ = "depts"
    __table_args__ = (
        # replaces the DynamoDB DEPTNAME# lock — DB enforces uniqueness
        UniqueConstraint("parent_id", "name", name="uq_dept_name_per_parent"),
    )

    node_id    = Column(UUID(as_uuid=True), ForeignKey("nodes.id", ondelete="CASCADE"), primary_key=True)
    parent_id  = Column(UUID(as_uuid=True), ForeignKey("nodes.id"), nullable=False)
    name       = Column(String(255), nullable=False)
    is_active  = Column(Boolean, nullable=False, default=True)
    created_by = Column(UUID(as_uuid=True))
    updated_by = Column(UUID(as_uuid=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)