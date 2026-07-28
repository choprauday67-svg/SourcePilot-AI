import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.infrastructure.db.base import Base

class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    requirement_id = Column(String, ForeignKey("procurement_requirements.id"), nullable=False, unique=True)
    summary = Column(Text, nullable=False) # AI Executive Summary Rationale
    recommended_supplier_id = Column(String, ForeignKey("suppliers.id"), nullable=True)
    comparison_matrix = Column(JSON, nullable=False) # Key metrics matrix comparing suppliers side-by-side
    generated_at = Column(DateTime, default=datetime.utcnow)
    generated_by_agent_version = Column(String, default="v1.0")

    requirement = relationship("ProcurementRequirement", back_populates="recommendation")
