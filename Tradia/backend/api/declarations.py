from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import Dict, Any

from config.database import get_db
from models import UserDeclaration, UserProcess, UserProcessItem
from schemas.declaration_schemas import (
    DeclarationResponse,
    UpdateDeclarationRequest,
    GeneratePdfResponse
)
from services.pdf_service import pdf_service
from utils.validators import validate_declaration_data

router = APIRouter(prefix="/api/declaration", tags=["declaration"])


@router.get("/{process_id}", response_model=DeclarationResponse)
async def get_declaration(
    process_id: str,
    db: Session = Depends(get_db)
):
    """Get declaration data for a process"""
    declaration = db.query(UserDeclaration).filter(UserDeclaration.process_id == process_id).first()
    if not declaration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Declaration not found"
        )
    
    return DeclarationResponse.from_orm(declaration)


@router.put("/{process_id}/update")
async def update_declaration(
    process_id: str,
    request: UpdateDeclarationRequest,
    db: Session = Depends(get_db)
):
    """Update declaration data"""
    declaration = db.query(UserDeclaration).filter(UserDeclaration.process_id == process_id).first()
    if not declaration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Declaration not found"
        )
    
    try:
        # Validate data
        validation_errors = validate_declaration_data(request.schema_details)
        if validation_errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Validation failed: {'; '.join(validation_errors)}"
            )
        
        # Update schema details
        declaration.schema_details.update(request.schema_details)
        
        db.commit()
        db.refresh(declaration)
        
        return DeclarationResponse.from_orm(declaration)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update declaration: {str(e)}"
        )


@router.post("/{process_id}/generate-pdf")
async def generate_declaration_pdf(
    process_id: str,
    db: Session = Depends(get_db)
):
    """Generate PDF declaration form"""
    try:
        # Get declaration data
        declaration = db.query(UserDeclaration).filter(UserDeclaration.process_id == process_id).first()
        if not declaration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Declaration not found"
            )
        
        # Get items
        items = db.query(UserProcessItem).filter(UserProcessItem.process_id == process_id).all()
        items_data = []
        
        for item in items:
            items_data.append({
                "item_title": item.item_title,
                "item_description": item.item_description,
                "item_type": item.item_type,
                "item_weight": float(item.item_weight) if item.item_weight else None,
                "item_weight_unit": item.item_weight_unit,
                "item_price": float(item.item_price) if item.item_price else None,
                "item_currency": item.item_currency
            })
        
        # Generate PDF
        pdf_bytes = pdf_service.generate_declaration_pdf(
            declaration.schema_details,
            items_data,
            declaration.declaration_type.value
        )
        
        # Return PDF as response
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=declaration_{process_id}.pdf"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF: {str(e)}"
        )
