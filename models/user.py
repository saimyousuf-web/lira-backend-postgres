from database import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True) 
    email = Column(String(255),unique=True,nullable=False,index=True)
    first_name = Column(String(255),nullable=False)
    last_name = Column(String(255),nullable=False)
    is_active = Column(Boolean,nullable=False,default=True)
    is_email_verified = Column(Boolean,nullable=False,default=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )


