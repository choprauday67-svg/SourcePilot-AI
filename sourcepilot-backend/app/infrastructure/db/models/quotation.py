import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.infrastructure.db.base import Base

class Quotation(Base):
    __tablename__ = "quotations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    rfq_id = Column(String, ForeignKey("rfqs.id"), nullable=True)
    rfq_dispatch_id = Column(String, ForeignKey("rfq_dispatches.id"), nullable=True)
    requirement_id = Column(String, ForeignKey("procurement_requirements.id"), nullable=True)
    supplier_id = Column(String, ForeignKey("suppliers.id"), nullable=False)
    quote_reference = Column(String, nullable=True)
    status = Column(String, default="received") # received, under_review, accepted, rejected
    raw_email_body = Column(Text, nullable=True)
    extracted_data = Column(JSON, nullable=False) # {unit_price, total_price, currency, moq, lead_time_days, warranty, payment_terms, validity_period, notes, quote_reference}
    extraction_confidence = Column(Float, default=1.0)
    received_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    rfq = relationship("RFQ")
    dispatch = relationship("RFQDispatch", back_populates="quotation")
    supplier = relationship("Supplier")
