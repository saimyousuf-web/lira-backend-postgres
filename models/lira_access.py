from sqlalchemy import Column, Boolean, ForeignKey, DateTime, func
from core.db import Base
from sqlalchemy.dialects.postgresql import UUID

class LiraAccess(Base):
    __tablename__ = "lira_access"

    uid = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    ndid = Column(UUID(as_uuid=True), ForeignKey("nodes.id", ondelete="CASCADE"), primary_key=True)

    rlid = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False)

    isact = Column(Boolean, nullable=False, default=True)
    isapr = Column(Boolean, nullable=False, default=False)

    crtat = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updat = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())