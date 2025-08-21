from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import uuid

from models.user_process_items import UserProcessItem
from schemas.item_schemas import ItemListResponse, ItemResponse
from schemas.process_schemas import ProcessResponse
from models import ProcessStatus
from config.database import get_db
from models import UserDocument, UserProcess
from schemas.document_schemas import (
    DocumentItemListResponse,
    DocumentResponse,
    DocumentListResponse,
    DocumentUploadResponse
)
from services.file_service import file_service
from services.ocr_service import ocr_service
from services.llm_service import llm_service
from tasks.background_tasks import process_documents
from utils.validators import validate_file_upload

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/upload/{process_id}", response_model=DocumentUploadResponse)
async def upload_documents(
    process_id: str,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """Upload documents for processing"""
    try:
        # Verify process exists
        process = db.query(UserProcess).filter(UserProcess.process_id == process_id).first()
        if not process:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Process not found"
            )
        
        process.status = ProcessStatus.CREATED
        db.add(process)
        db.commit()
        
        
        if not files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No files provided"
            )
        
        
        uploaded_documents = []
        document_ids = []
        
        for file in files:
            # Validate file
            validation_errors = validate_file_upload(file.filename, file.content_type)
            if validation_errors:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File validation failed: {'; '.join(validation_errors)}"
                )
            
            try:
                # Save file
                file_path = await file_service.save_file(file, "default")  # TODO: Get actual user_id
                
                # Create document record
                document = UserDocument(
                    document_name=file.filename,
                    document_type=file.content_type,
                    file_path=file_path,
                    process_id=process_id
                )
                db.add(document)
                db.flush()  # Get document_id
                
                uploaded_documents.append(DocumentResponse.from_orm(document))
                document_ids.append(str(document.document_id))
                
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to save file {file.filename}: {str(e)}"
                )
        
        db.commit()
        
        # Start background processing
        if document_ids:
            process_documents.delay(process_id, document_ids)
        
        return DocumentUploadResponse(
            message="Files uploaded successfully",
            uploaded_files=uploaded_documents
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


@router.get("/{process_id}", response_model=DocumentListResponse)
async def get_process_documents(
    process_id: str,
    db: Session = Depends(get_db)
):
    """Get all documents for a process"""
    # Verify process exists
    process = db.query(UserProcess).filter(UserProcess.process_id == process_id).first()
    if not process:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Process not found"
        )
    
    documents = db.query(UserDocument).filter(UserDocument.process_id == process_id).all()
    total = len(documents)
    
    return DocumentListResponse(
        documents=[DocumentResponse.from_orm(doc) for doc in documents],
        process=ProcessResponse.from_orm(process),
        total=total
    )


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """Delete a document"""
    document = db.query(UserDocument).filter(UserDocument.document_id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    try:
        # Delete file from storage
        file_service.delete_file(document.file_path)
        
        # Delete database record
        db.delete(document)
        db.commit()
        
        return {"message": "Document deleted successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )

@router.get("/{document_id}/items", response_model=DocumentItemListResponse)
def get_document_with_items(
    document_id: str,
    db: Session = Depends(get_db)
):
    """GET a document"""
    document = db.query(UserDocument).filter(UserDocument.document_id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    try:
        # GET document items
        items = db.query(UserProcessItem).filter(UserProcessItem.document_id == document_id).all()
        
        return DocumentItemListResponse(
            document=DocumentResponse.from_orm(document),
            items=ItemListResponse(
                items=[ItemResponse.from_orm(item) for item in items],
                total=len(items)
            )
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load document's items: {str(e)}"
        )
