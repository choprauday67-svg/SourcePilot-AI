import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from app.infrastructure.db.base import Base

class RequirementSupplierMatch(Base):
    __tablename__ = "requirement_supplier_matches"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    requirement_id = Column(String, ForeignKey("procurement_requirements.id"), nullable=False)
    supplier_id = Column(String, ForeignKey("suppliers.id"), nullable=False)
    rank_score = Column(Float, nullable=False)
    rank_explanation = Column(JSON, nullable=False) # Factor breakdown & reasoning
    selected_by_user = Column(Boolean, default=False)
    selected_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    requirement = relationship("ProcurementRequirement", back_populates="matches")
    supplier = relationship("Supplier", back_populates="matches")
