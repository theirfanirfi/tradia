from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from config.database import Base
import uuid


class UserDocument(Base):
    __tablename__ = "user_documents"
    
    document_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_name = Column(String(255), nullable=False)
    document_type = Column(String(20), nullable=False)
    file_path = Column(String(500), nullable=False)
    ocr_text = Column(Text, nullable=True)
    llm_response = Column(JSONB, nullable=True)
    process_id = Column(UUID(as_uuid=True), ForeignKey("user_process.process_id"), nullable=False)
    document_status = Column(String(50), nullable=False, default="uploaded")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    process = relationship("UserProcess", back_populates="documents")
    items = relationship("UserProcessItem", back_populates="document", cascade="all, delete-orphan")
