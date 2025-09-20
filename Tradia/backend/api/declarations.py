from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import Dict, Any

from config.database import get_db
from models import UserDeclaration, UserProcess, UserProcessItem
from models.auth import User
from schemas.declaration_schemas import (
    DeclarationResponse,
    UpdateDeclarationRequest,
    GeneratePdfResponse
)
from services.pdf_service import pdf_service
from utils.auth_dependencies import get_current_user
from utils.validators import validate_declaration_data
from tasks.background_tasks import task_b650_extract_section_a_information
from schemas.B650.import_section_a import B650SectionAHeader

router = APIRouter(prefix="/api/declaration", tags=["declaration"])


@router.get("/import/{process_id}/section_a", response_model=DeclarationResponse)
async def get_declaration(
    process_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get declaration data for a process"""
    declaration = db.query(UserDeclaration).filter(UserDeclaration.process_id == process_id).first()
    if not declaration:
        task_b650_extract_section_a_information.delay(process_id)
        raise HTTPException(
            status_code=status.HTTP_201_CREATED,
            detail="Declarations being ready"
        )
        # return DeclarationResponse.from_orm(declaration)
    
    return DeclarationResponse.from_orm(declaration)


@router.put("/import/{process_id}/update/section_a", response_model=DeclarationResponse)
async def update_declaration(
    process_id: str,
    request: B650SectionAHeader,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update declaration data"""
    declaration = db.query(UserDeclaration).filter(UserDeclaration.process_id == process_id).first()
    if not declaration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Declaration not found"
        )
    
    print(request)
    
    try:
        # Validate data
        # validation_errors = validate_declaration_data(request.schema_details)
        # if validation_errors:
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail=f"Validation failed: {'; '.join(validation_errors)}"
        #     )
        
        # Update schema details
        # section_a = B650SectionAHeader(**request)
        json_str = request.model_dump(exclude_none=False, mode='json')
        declaration.import_declaration_section_a = json_str
        db.add(declaration)
        
        db.commit()
        db.refresh(declaration)
        
        return DeclarationResponse.from_orm(declaration)
        
    except Exception as ee:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update declaration: {str(ee)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update declarationn: {str(e)}"
        )


@router.post("/{process_id}/generate-pdf")
async def generate_declaration_pdf(
    process_id: str,
    current_user: User = Depends(get_current_user),
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
