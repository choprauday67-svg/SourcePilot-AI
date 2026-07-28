from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field

class RequirementCreate(BaseModel):
    title: Optional[str] = None
    raw_text: str = Field(..., min_length=5, description="Natural language procurement requirement prompt")

class RequirementUpdate(BaseModel):
    title: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None
    category: Optional[str] = None
    status: Optional[str] = None

class RequirementResponse(BaseModel):
    id: str
    organization_id: str
    created_by: str
    title: str
    raw_text: str
    structured_data: Optional[Dict[str, Any]] = None
    category: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
