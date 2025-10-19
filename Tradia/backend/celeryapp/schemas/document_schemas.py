from pydantic import BaseModel, UUID4
from typing import Optional, List
from datetime import datetime

from schemas.item_schemas import ItemListResponse
from schemas.process_schemas import ProcessResponse


class DocumentResponse(BaseModel):
    document_id: UUID4
    document_name: str
    document_type: str
    file_path: str
    ocr_text: Optional[str]
    llm_response: Optional[dict]
    process_id: UUID4
    created_at: datetime
    processed_at: Optional[datetime]

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    process: ProcessResponse
    total: int

class DocumentItemListResponse(BaseModel):
    document: DocumentResponse
    items: ItemListResponse


class DocumentUploadResponse(BaseModel):
    message: str
    uploaded_files: List[DocumentResponse]
