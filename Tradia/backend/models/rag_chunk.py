from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from config.database import Base
import uuid
from pgvector.sqlalchemy import Vector


class RagChunk(Base):
    __tablename__ = "rag_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(String, index=True, nullable=True)
    chunk_id = Column(String, unique=True, nullable=False, index=True)
    text = Column(Text, nullable=False)
    embedding = Column(Vector(1024))  # set dimension to match mxbai-embed-large
    metadata = Column(JSONB, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
