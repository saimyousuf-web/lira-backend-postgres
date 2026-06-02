from core.db import Base
from sqlalchemy import Column, String, Text
from sqlalchemy.dialects.postgresql import UUID
import uuid


class Role(Base):
    __tablename__ = "roles"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    name = Column(
        String(255),
        unique=True,
        nullable=False
    )

    description = Column(
        Text,
        nullable=True
    )