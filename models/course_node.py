from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from core.db import Base


class CourseNode(Base):
    __tablename__ = "course_node"

    __table_args__ = (
        Index("idx_course_node_node", "ndid"),
        Index("idx_course_node_course", "cid"),
    )

    cid = Column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        primary_key=True,
    )

    ndid = Column(
        UUID(as_uuid=True),
        ForeignKey("nodes.id", ondelete="CASCADE"),
        primary_key=True,
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

    crtby = Column(
        UUID(as_uuid=True),
        nullable=True,
    )

    updby = Column(
        UUID(as_uuid=True),
        nullable=True,
    )