from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from config.database import Base
import uuid


class UserProcessItem(Base):
    __tablename__ = "user_process_items"
    
    item_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    process_id = Column(UUID(as_uuid=True), ForeignKey("user_process.process_id"), nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey("user_documents.document_id"), nullable=False)
    item_title = Column(String(255), nullable=False)
    item_description = Column(Text, nullable=True)
    item_type = Column(String(100), nullable=True)
    item_weight = Column(Numeric(10, 3), nullable=True)
    item_weight_unit = Column(String(10), nullable=True)
    item_price = Column(Numeric(12, 2), nullable=True)
    item_currency = Column(String(3), nullable=True)
    item_hs_code = Column(String(15), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    process = relationship("UserProcess", back_populates="items")
    document = relationship("UserDocument", back_populates="items")
