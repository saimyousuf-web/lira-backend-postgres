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
    __tablename__ = "courses"

    __table_args__ = (
        # Index("idx_courses_status", "status"),
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

    nm = Column(
        String(255),
        nullable=False,
    )

    dsc = Column(
        Text,
        nullable=True,
    )

    sts = Column(
        String(50),
        nullable=False,
        server_default="DRAFT",
    )

    no_of_modules = Column(
        Integer,
        nullable=False,
        server_default="0",
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