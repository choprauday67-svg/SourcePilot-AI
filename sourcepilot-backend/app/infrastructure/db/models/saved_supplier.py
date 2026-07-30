"""
SavedSupplier — Phase 3 Saved Supplier Library ORM Model

Stores organization-wide bookmarked/preferred suppliers with tags, notes,
category assignment, and status. Allows selecting saved suppliers directly for RFQs.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.infrastructure.db.base import Base


class SavedSupplier(Base):
    __tablename__ = "saved_suppliers"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    supplier_id = Column(String, ForeignKey("suppliers.id"), nullable=False, index=True)
    saved_by_user_id = Column(String, ForeignKey("users.id"), nullable=False)
    category = Column(String, nullable=True, default="General")
    status = Column(String, default="preferred")  # preferred, active, archived
    tags = Column(JSON, default=list)  # e.g., ["ISO Certified", "Fast Delivery", "Tier 1"]
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    supplier = relationship("Supplier")
    user = relationship("User")
