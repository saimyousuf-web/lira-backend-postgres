from sqlalchemy import Column, Boolean, ForeignKey, DateTime, UniqueConstraint, func
from sqlalchemy.orm import relationship
from core.db import Base
from sqlalchemy.dialects.postgresql import UUID

class LiraAccess(Base):
    __tablename__ = "lira_access"

    uid = Column(String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    ndid = Column(String, ForeignKey("nodes.id", ondelete="CASCADE"), primary_key=True)

    rlid = Column(String, ForeignKey("roles.id"), nullable=False)

    isact = Column(Boolean, nullable=False, default=True)
    isapr = Column(Boolean, nullable=False, default=False)

    crtat = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updat = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())