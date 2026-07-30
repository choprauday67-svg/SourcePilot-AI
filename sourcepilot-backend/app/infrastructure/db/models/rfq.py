import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from app.infrastructure.db.base import Base

class RFQ(Base):
    __tablename__ = "rfqs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    requirement_id = Column(String, ForeignKey("procurement_requirements.id"), nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False) # Markdown/Rich text RFQ body
    version = Column(Integer, default=1)
    status = Column(String, default="draft") # draft, approved, sent
    generated_by_agent_version = Column(String, default="v1.0")
    approved_by = Column(String, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    requirement = relationship("ProcurementRequirement", back_populates="rfqs")
    dispatches = relationship("RFQDispatch", back_populates="rfq", cascade="all, delete-orphan")
    approvals = relationship("RFQApproval", back_populates="rfq", cascade="all, delete-orphan")


class RFQApproval(Base):
    """Phase 3 — Multi-approver RFQ workflow approval record."""
    __tablename__ = "rfq_approvals"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    rfq_id = Column(String, ForeignKey("rfqs.id"), nullable=False, index=True)
    step_number = Column(Integer, default=1)
    role_required = Column(String, default="approver")  # buyer, approver, admin, director
    approver_id = Column(String, ForeignKey("users.id"), nullable=True)
    status = Column(String, default="pending")  # pending, approved, rejected
    comments = Column(Text, nullable=True)
    decided_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    rfq = relationship("RFQ", back_populates="approvals")


class RFQDispatch(Base):
    __tablename__ = "rfq_dispatches"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    rfq_id = Column(String, ForeignKey("rfqs.id"), nullable=False)
    supplier_id = Column(String, ForeignKey("suppliers.id"), nullable=False)
    supplier_contact_id = Column(String, ForeignKey("supplier_contacts.id"), nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
    delivery_status = Column(String, default="queued") # queued, sent, delivered, bounced, opened, replied
    provider_message_id = Column(String, nullable=True)
    follow_up_count = Column(Integer, default=0)
    last_follow_up_at = Column(DateTime, nullable=True)

    rfq = relationship("RFQ", back_populates="dispatches")
    quotation = relationship("Quotation", back_populates="dispatch", uselist=False)
