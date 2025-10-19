from pydantic import BaseModel, UUID4
from typing import Optional, Dict, Any
from datetime import datetime


class DeclarationResponse(BaseModel):
    declaration_id: UUID4
    declaration_type: str
    import_declaration_section_a: Dict[str, Any]
    import_declaration_section_b: Dict[str, Any]
    import_declaration_section_c: Dict[str, Any]
    process_id: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UpdateDeclarationRequest(BaseModel):
    schema_details: Dict[str, Any]


class GeneratePdfResponse(BaseModel):
    message: str
    pdf_url: Optional[str] = None
    pdf_data: Optional[bytes] = None

