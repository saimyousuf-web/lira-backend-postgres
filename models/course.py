import uuid

from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    DateTime,
    Index,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from core.db import Base


class Course(Base):
    __tablename__ = "course"

    __table_args__ = (
        Index("idx_courses_status", "status"),
        CheckConstraint(
            "status IN ('DRAFT', 'PUBLISHED', 'RETIRED')",
            name="ck_course_status",
        ),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name = Column(
        String(255),
        nullable=False,
    )

    description = Column(
        Text,
        nullable=True,
    )

    status = Column(
        String(50),
        nullable=False,
        server_default="DRAFT",
    )

    no_of_modules = Column(
        Integer,
        nullable=False,
        server_default="0",
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