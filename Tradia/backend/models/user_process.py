from sqlalchemy import Column, String, DateTime, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from config.database import Base
import uuid
import enum


class ProcessStatus(str, enum.Enum):
    CREATED = "Created"
    EXTRACTING = "Extracting"
    UNDERSTANDING = "Understanding"
    GENERATING = "Generating"
    DONE = "Done"
    ERROR = "error"


class UserProcess(Base):
    __tablename__ = "user_process"
    
    process_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=True)  # Will be linked to auth system
    process_name = Column(String(255), nullable=False)
    status = Column(Enum(ProcessStatus), default=ProcessStatus.CREATED, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
