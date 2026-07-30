"""
Phase 4 Email Draft Schemas
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class EmailDraftUpdate(BaseModel):
    subject: Optional[str] = None
    body_markdown: Optional[str] = None
    recipient_email: Optional[str] = None


class ApproveAndSendDraftRequest(BaseModel):
    connected_account_id: Optional[str] = None  # Mailbox to send from (optional fallback to sandbox)
    approval_notes: Optional[str] = ""


class EmailDraftResponse(BaseModel):
    id: str
    rfq_id: str
    supplier_id: str
    supplier_name: Optional[str] = None
    connected_account_id: Optional[str] = None
    created_by_user_id: str
    draft_type: str
    recipient_email: str
    recipient_name: Optional[str] = None
    subject: str
    body_markdown: str
    delivery_status: str
    approved_by_user_id: Optional[str] = None
    approved_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    provider_message_id: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SyncRepliesResponse(BaseModel):
    synced_messages_count: int
    quotations_extracted_count: int
    details: List[str]
