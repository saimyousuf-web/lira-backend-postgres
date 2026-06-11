import uuid

from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from core.db import Base


class ModuleUpdateLog(Base):
    __tablename__ = "module_update_logs"

    __table_args__ = (
        Index("idx_mul_cid_ndid", "cid", "ndid"),
        Index("idx_mul_moid", "moid"),
        Index("idx_mul_crtat", "crtat"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

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

    moid = Column(
        UUID(as_uuid=True),
        ForeignKey("module.id", ondelete="CASCADE"),
        nullable=False,
    )

    action = Column(String(100), nullable=False)

    prev_sts = Column(String(50), nullable=True)
    new_sts = Column(String(50), nullable=True)

    crtby = Column(UUID(as_uuid=True), nullable=True)

    crtat = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
