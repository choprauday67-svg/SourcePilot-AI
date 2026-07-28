from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

class RFQUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

class RFQDispatchResponse(BaseModel):
    id: str
    supplier_id: str
    supplier_contact_id: str
    sent_at: datetime
    delivery_status: str
    provider_message_id: Optional[str] = None

    class Config:
        from_attributes = True

class RFQResponse(BaseModel):
    id: str
    requirement_id: str
    title: str
    content: str
    version: int
    status: str
    approved_at: Optional[datetime] = None
    created_at: datetime
    dispatches: List[RFQDispatchResponse] = []

    class Config:
        from_attributes = True
