from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime, UniqueConstraint, func
from sqlalchemy.orm import relationship
from core.db import Base

class LiraAccess(Base):
    __tablename__ = "lira_access"

    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    node_id = Column(String, ForeignKey("nodes.id", ondelete="CASCADE"), primary_key=True)

    role_id = Column(String, ForeignKey("roles.id"), nullable=False)

    is_active = Column(Boolean, nullable=False, default=True)
    is_approved = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())