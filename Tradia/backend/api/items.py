from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from config.database import get_db
from models import UserProcessItem, UserProcess
from schemas.item_schemas import (
    CreateItemRequest,
    UpdateItemRequest,
    ItemResponse,
    ItemListResponse
)
from utils.validators import validate_item_data

router = APIRouter(prefix="/api/items", tags=["items"])


@router.get("/{process_id}", response_model=ItemListResponse)
async def get_process_items(
    process_id: str,
    db: Session = Depends(get_db)
):
    """Get all items for a process"""
    # Verify process exists
    process = db.query(UserProcess).filter(UserProcess.process_id == process_id).first()
    if not process:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Process not found"
        )
    
    items = db.query(UserProcessItem).filter(UserProcessItem.process_id == process_id).all()
    total = len(items)
    
    return ItemListResponse(
        items=[ItemResponse.from_orm(item) for item in items],
        total=total
    )


@router.put("/{item_id}")
async def update_item(
    item_id: str,
    request: UpdateItemRequest,
    db: Session = Depends(get_db)
):
    """Update an item"""
    item = db.query(UserProcessItem).filter(UserProcessItem.item_id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    
    try:
        # Validate updated data
        validation_errors = validate_item_data(request.dict(exclude_unset=True))
        if validation_errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Validation failed: {'; '.join(validation_errors)}"
            )
        
        # Update fields
        update_data = request.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(item, field, value)
        
        db.commit()
        db.refresh(item)
        
        return ItemResponse.from_orm(item)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update item: {str(e)}"
        )


@router.delete("/{item_id}")
async def delete_item(
    item_id: str,
    db: Session = Depends(get_db)
):
    """Delete an item"""
    item = db.query(UserProcessItem).filter(UserProcessItem.item_id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    
    try:
        db.delete(item)
        db.commit()
        
        return {"message": "Item deleted successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete item: {str(e)}"
        )
