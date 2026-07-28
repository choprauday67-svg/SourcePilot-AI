import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.infrastructure.db.base import Base

class ProcurementRequirement(Base):
    __tablename__ = "procurement_requirements"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    raw_text = Column(Text, nullable=False)
    structured_data = Column(JSON, nullable=True) # {product, quantity, budget, location, timeline, specs, certifications}
    category = Column(String, nullable=True, index=True)
    status = Column(String, default="draft") # draft, discovering, ranked, rfq_sent, quoted, completed, archived
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = relationship("Organization", back_populates="requirements")
    created_by_user = relationship("User", back_populates="requirements")
    matches = relationship("RequirementSupplierMatch", back_populates="requirement", cascade="all, delete-orphan")
    rfqs = relationship("RFQ", back_populates="requirement", cascade="all, delete-orphan")
    recommendation = relationship("Recommendation", back_populates="requirement", uselist=False)
