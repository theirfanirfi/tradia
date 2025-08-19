from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import json
import os

from config.database import get_db
from models import UserProcess, UserDeclaration, DeclarationType, ProcessStatus
from schemas.process_schemas import (
    CreateProcessRequest,
    ProcessResponse,
    ProcessStatusResponse,
    ProcessListResponse
)
from utils.validators import validate_declaration_type
from utils.status_manager import get_process_summary

router = APIRouter(prefix="/api/process", tags=["process"])


@router.post("/create", response_model=ProcessResponse)
async def create_process(
    request: CreateProcessRequest,
    db: Session = Depends(get_db)
):
    print('request', request.declaration_type)
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
            declaration_schema=declaration_schema,
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
    db: Session = Depends(get_db)
):
    """Get process details"""
    process = db.query(UserProcess).filter(UserProcess.process_id == process_id).first()
    if not process:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Process not found"
        )
    
    return ProcessResponse.from_orm(process)


@router.get("/{process_id}/status", response_model=ProcessStatusResponse)
async def get_process_status(
    process_id: str,
    db: Session = Depends(get_db)
):
    """Get process status and progress"""
    from utils.status_manager import calculate_progress
    
    process = db.query(UserProcess).filter(UserProcess.process_id == process_id).first()
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
    db: Session = Depends(get_db)
):
    """List all processes"""
    processes = db.query(UserProcess).offset(skip).limit(limit).all()
    total = db.query(UserProcess).count()
    
    return ProcessListResponse(
        processes=[ProcessResponse.from_orm(p) for p in processes],
        total=total
    )
