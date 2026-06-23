from sqlalchemy.orm import Mapped, mapped_column

from core.db import Base
from sqlalchemy import Column, String, Text, DateTime, Boolean, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from models.enums.feedback_status import FeedbackStatus


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    uid = Column(UUID(as_uuid=True), nullable=False)
    cid = Column(UUID(as_uuid=True), nullable=False)
    convid = Column(UUID(as_uuid=True), nullable=False)
    sessid = Column(UUID(as_uuid=True), nullable=False)
    # sessid = evid 

    sessquery = Column(Text, nullable=False)

    feedtxt = Column(Text, nullable=True)

    feedty = Column(String, nullable=False)
    rsn = Column(String, nullable=True)

    smeres: Mapped[str | None] = mapped_column(
    Text,
    nullable=True)


    isact = Column(Boolean, nullable=False, default=True)

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

    crtby: Mapped[uuid.UUID | None] = mapped_column(
    UUID(as_uuid=True),
    nullable=True
)
    updby = Column(UUID(as_uuid=True), nullable=True)
    ndid = Column(UUID(as_uuid=True), nullable=False)
    sts = Column(
    Enum(
        FeedbackStatus,
        values_callable=lambda x: [e.value for e in x]
    ),
    nullable=False,
    server_default=FeedbackStatus.PENDING.value,
)

        