from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from core.db import Base


class CatCourse(Base):
    __tablename__ = "cat_course"

    __table_args__ = (
        Index("idx_cat_course_course", "cid"),
        Index("idx_cat_course_category", "catid"),
    )

    catid = Column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="CASCADE"),
        primary_key=True,
    )

    cid = Column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
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