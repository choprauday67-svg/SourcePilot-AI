import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.infrastructure.db.base import Base

class Quotation(Base):
    __tablename__ = "quotations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    rfq_dispatch_id = Column(String, ForeignKey("rfq_dispatches.id"), nullable=True)
    requirement_id = Column(String, ForeignKey("procurement_requirements.id"), nullable=True)  # nullable for webhook-sourced quotes
    supplier_id = Column(String, ForeignKey("suppliers.id"), nullable=False)
    raw_email_body = Column(Text, nullable=True)
    extracted_data = Column(JSON, nullable=False) # {unit_price, total_price, currency, moq, lead_time_days, warranty, payment_terms, validity_period}
    extraction_confidence = Column(Float, default=1.0)
    received_at = Column(DateTime, default=datetime.utcnow)

    dispatch = relationship("RFQDispatch", back_populates="quotation")
    supplier = relationship("Supplier")
