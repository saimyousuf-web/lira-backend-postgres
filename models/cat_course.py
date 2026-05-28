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
        Index("idx_cat_course_course", "course_id"),
        Index("idx_cat_course_category", "category_id"),
    )

    category_id = Column(
        UUID(as_uuid=True),
        ForeignKey("category.id", ondelete="CASCADE"),
        primary_key=True,
    )

    course_id = Column(
        UUID(as_uuid=True),
        ForeignKey("course.id", ondelete="CASCADE"),
        primary_key=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    created_by = Column(
        UUID(as_uuid=True),
        nullable=True,
    )

    updated_by = Column(
        UUID(as_uuid=True),
        nullable=True,
    )