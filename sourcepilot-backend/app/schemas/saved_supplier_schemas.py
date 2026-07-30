"""
SavedSupplier Pydantic Schemas — Phase 3
"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from app.schemas.supplier_schemas import SupplierResponse


class SavedSupplierCreate(BaseModel):
    supplier_id: str
    category: Optional[str] = "General"
    status: Optional[str] = "preferred"
    tags: Optional[List[str]] = []
    notes: Optional[str] = ""


class SavedSupplierUpdate(BaseModel):
    category: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None


class SavedSupplierResponse(BaseModel):
    id: str
    organization_id: str
    supplier_id: str
    saved_by_user_id: str
    category: Optional[str]
    status: str
    tags: List[str]
    notes: Optional[str]
    created_at: datetime
    supplier: SupplierResponse

    model_config = {"from_attributes": True}


class SelectSavedSuppliersRequest(BaseModel):
    supplier_ids: List[str]
