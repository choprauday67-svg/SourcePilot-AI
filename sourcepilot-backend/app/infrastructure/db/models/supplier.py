import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from app.infrastructure.db.base import Base

class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_name = Column(String, nullable=False, index=True)
    website = Column(String, nullable=True)
    canonical_domain = Column(String, unique=True, index=True, nullable=True)
    location_country = Column(String, nullable=True)
    location_city = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_enriched_at = Column(DateTime, nullable=True)

    contacts = relationship("SupplierContact", back_populates="supplier", cascade="all, delete-orphan")
    profiles = relationship("SupplierProfile", back_populates="supplier", cascade="all, delete-orphan")
    matches = relationship("RequirementSupplierMatch", back_populates="supplier")

class SupplierContact(Base):
    __tablename__ = "supplier_contacts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    supplier_id = Column(String, ForeignKey("suppliers.id"), nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    contact_name = Column(String, nullable=True)
    is_primary = Column(Boolean, default=True)
    source_connector = Column(String, default="web_search")
    confidence_score = Column(Float, default=1.0)

    supplier = relationship("Supplier", back_populates="contacts")

class SupplierProfile(Base):
    __tablename__ = "supplier_profiles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    supplier_id = Column(String, ForeignKey("suppliers.id"), nullable=False)
    requirement_id = Column(String, ForeignKey("procurement_requirements.id"), nullable=True)
    reviews_summary = Column(JSON, nullable=True)
    rating = Column(Float, default=4.5)
    certifications = Column(JSON, default=list) # e.g. ["ISO 9001", "CE"]
    moq = Column(String, nullable=True)
    warranty_terms = Column(String, nullable=True)
    lead_time_days = Column(Float, nullable=True)
    estimated_price_range = Column(JSON, nullable=True)
    raw_sources = Column(JSON, default=list) # [{url, connector, fetched_at}]
    trust_score = Column(Float, default=85.0)
    risk_flags = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    supplier = relationship("Supplier", back_populates="profiles")
