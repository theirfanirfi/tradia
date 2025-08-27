from pydantic import BaseModel, UUID4
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class CreateItemRequest(BaseModel):
    item_title: str
    item_description: Optional[str] = None
    item_type: Optional[str] = None
    item_weight: Optional[Decimal] = None
    item_weight_unit: Optional[str] = None
    item_price: Optional[Decimal] = None
    item_currency: Optional[str] = None


class UpdateItemRequest(BaseModel):
    item_title: Optional[str] = None
    item_description: Optional[str] = None
    item_type: Optional[str] = None
    item_weight: Optional[Decimal] = None
    item_weight_unit: Optional[str] = None
    item_price: Optional[Decimal] = None
    item_currency: Optional[str] = None


class ItemResponse(BaseModel):
    item_id: UUID4
    process_id: UUID4
    item_title: str
    item_description: Optional[str]
    item_type: Optional[str]
    item_weight: Optional[Decimal]
    item_weight_unit: Optional[str]
    item_price: Optional[Decimal]
    item_currency: Optional[str]
    item_hs_code: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ItemListResponse(BaseModel):
    items: List[ItemResponse]
    total: int
