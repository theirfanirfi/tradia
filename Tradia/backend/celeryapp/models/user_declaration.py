from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from config.database import Base
import uuid
import enum


class DeclarationType(str, enum.Enum):
    IMPORT = "import"
    EXPORT = "export"


class UserDeclaration(Base):
    __tablename__ = "user_declaration"
    
    declaration_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    declaration_type = Column(Enum(DeclarationType), nullable=False)
    import_declaration_section_a= Column(JSONB, default={})
    import_declaration_section_b= Column(JSONB, default={})
    import_declaration_section_c= Column(JSONB, default={})
    process_id = Column(UUID(as_uuid=True), ForeignKey("user_process.process_id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    process = relationship("UserProcess", back_populates="declarations")
