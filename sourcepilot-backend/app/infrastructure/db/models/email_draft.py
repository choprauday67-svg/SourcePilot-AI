import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.infrastructure.db.base import Base

class EmailDraft(Base):
    """
    Phase 4 — Email Draft & Human Approval Log.
    Tracks outbound email drafts (initial RFQ dispatches and follow-up reminders).
    AI ONLY generates drafts in delivery_status='draft'.
    Delivery transitions: draft -> sending -> sent / failed / discarded.
    Human approval is explicitly recorded via approved_by_user_id & approved_at.
    """
    __tablename__ = "email_drafts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    rfq_id = Column(String, ForeignKey("rfqs.id"), nullable=False, index=True)
    supplier_id = Column(String, ForeignKey("suppliers.id"), nullable=False, index=True)
    connected_account_id = Column(String, ForeignKey("connected_accounts.id"), nullable=True)
    created_by_user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    draft_type = Column(String, default="initial_rfq")  # "initial_rfq", "follow_up_reminder"
    recipient_email = Column(String, nullable=False)
    recipient_name = Column(String, nullable=True)
    subject = Column(String, nullable=False)
    body_markdown = Column(Text, nullable=False)
    
    # State tracking: draft -> sending -> sent / failed / discarded
    delivery_status = Column(String, default="draft")
    
    # Explicit human approval record
    approved_by_user_id = Column(String, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    sent_at = Column(DateTime, nullable=True)
    provider_message_id = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    rfq = relationship("RFQ")
    supplier = relationship("Supplier")
    connected_account = relationship("ConnectedAccount")
