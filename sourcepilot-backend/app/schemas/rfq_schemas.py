from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

class RFQUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

class RFQApprovalResponse(BaseModel):
    id: str
    rfq_id: str
    step_number: int
    role_required: str
    approver_id: Optional[str] = None
    status: str
    comments: Optional[str] = None
    decided_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ApproveStepRequest(BaseModel):
    step_number: int
    comments: Optional[str] = None

class RejectStepRequest(BaseModel):
    step_number: int
    comments: str

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
    approvals: List[RFQApprovalResponse] = []

    class Config:
        from_attributes = True
