from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import json
import os

from config.database import get_db
from models import UserProcess, UserDeclaration, DeclarationType, ProcessStatus
from models.auth import User
from models.user_documents import UserDocument
from models.user_process_items import UserProcessItem
from schemas.process_schemas import (
    CreateProcessRequest,
    ProcessResponse,
    ProcessStatusResponse,
    ProcessListResponse
)
from services.file_service import file_service
from utils.auth_dependencies import get_current_active_user, get_current_user
from utils.validators import validate_declaration_type
from utils.status_manager import get_process_summary

router = APIRouter(prefix="/api/process", tags=["process"])


@router.post("/create", response_model=ProcessResponse)
async def create_process(
    request: CreateProcessRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    print('request', request.declaration_type, current_user)
    """Create a new declaration process"""
    try:
        # Validate declaration type
        if not validate_declaration_type(request.declaration_type):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid declaration type. Must be 'import' or 'export'"
            )
        
        # Create process
        process = UserProcess(
            process_name=request.name,
            user_id=current_user.user_id,
            status=ProcessStatus.CREATED
        )
        db.add(process)
        db.flush()  # Get the process_id
        print('process', process.process_id)
        
        # Load declaration schema template
        schema_file = f"templates/{request.declaration_type}_form.json"
        print(schema_file)
        declaration_schema = {}
        
        if os.path.exists(schema_file):
            with open(schema_file, 'r') as f:
                declaration_schema = json.load(f)
        
        # print(declaration_schema)
        # Create declaration entry
        declaration = UserDeclaration(
            declaration_type=DeclarationType(request.declaration_type),
            # declaration_schema=declaration_schema,
            process_id=process.process_id
        )
        db.add(declaration)
        
        db.commit()
        db.refresh(process)
        print('process', process.process_name)
        print('declaration', declaration.declaration_type)
        
        return ProcessResponse.from_orm(process)
        
    except Exception as e:
        db.rollback()
        print('exception ',e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create process: {str(e)}"
        )


@router.get("/{process_id}", response_model=ProcessResponse)
async def get_process(
    process_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get process details"""
    # print("current_user", current_user)
    process = db.query(UserProcess).filter(
        UserProcess.process_id == process_id,
        UserProcess.user_id == current_user.user_id
    ).first()
    if not process:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Process not found"
        )
    return ProcessResponse.from_orm(process)


@router.get("/{process_id}/status", response_model=ProcessStatusResponse)
async def get_process_status(
    process_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get process status and progress"""
    from utils.status_manager import calculate_progress
    
    process = db.query(UserProcess).filter(
        UserProcess.process_id == process_id,
        UserProcess.user_id == current_user.user_id
        ).first()
    if not process:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Process not found"
        )
    
    progress = calculate_progress(process_id)
    
    return ProcessStatusResponse(
        status=process.status,
        progress=progress,
        message=f"Process is {process.status.value}"
    )


@router.get("/", response_model=ProcessListResponse)
async def list_processes(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all processes"""
    print('current_user', current_user)
    processes = db.query(UserProcess).filter(UserProcess.user_id == current_user.user_id).all()
    total = db.query(UserProcess).count()
    
    return ProcessListResponse(
        processes=[ProcessResponse.from_orm(p) for p in processes],
        total=total
    )

@router.delete("/{process_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_process(
    process_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a process and all associated rows (items, documents, declarations)"""
    try:
        process = db.query(UserProcess).filter(
            UserProcess.process_id == process_id,
            UserProcess.user_id == current_user.user_id
        ).first()
        if not process:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Process not found"
            )

        # Delete process items first
        db.query(UserProcessItem).filter(UserProcessItem.process_id == process_id).delete(synchronize_session=False)

        # Delete document files from storage, then document rows
        documents = db.query(UserDocument).filter(UserDocument.process_id == process_id).all()
        for doc in documents:
            try:
                if doc.file_path:
                    file_service.delete_file(doc.file_path)
            except Exception as fe:
                print(f"failed to delete file for document {getattr(doc, 'document_id', None)}: {fe}")

        db.query(UserDocument).filter(UserDocument.process_id == process_id).delete(synchronize_session=False)

        # Delete declarations
        db.query(UserDeclaration).filter(UserDeclaration.process_id == process_id).delete(synchronize_session=False)

        # Delete the process itself
        db.delete(process)

        db.commit()
        print('deleted process', process_id)
        return
    except Exception as e:
        db.rollback()
        print('exception ', e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete process: {str(e)}"
        )