from pydantic import BaseModel, UUID4
from typing import Optional, List
from datetime import datetime
from models.user_process import ProcessStatus


class CreateProcessRequest(BaseModel):
    name: str
    declaration_type: str  # "import" or "export"


class ProcessResponse(BaseModel):
    process_id: UUID4
    user_id: Optional[UUID4]
    process_name: str
    status: ProcessStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProcessStatusResponse(BaseModel):
    status: ProcessStatus
    progress: int
    message: Optional[str] = None


class ProcessListResponse(BaseModel):
    processes: List[ProcessResponse]
    total: int
