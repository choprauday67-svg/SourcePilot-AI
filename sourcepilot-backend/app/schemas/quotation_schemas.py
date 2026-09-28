from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field

class ManualQuotationCreate(BaseModel):
    requirement_id: Optional[str] = None
    rfq_id: Optional[str] = None
    supplier_id: str
    quote_reference: Optional[str] = None
    unit_price: float = Field(..., gt=0, description="Unit price must be positive")
    total_price: float = Field(..., gt=0, description="Total price must be positive")
    currency: str = Field("USD", max_length=10)
    moq: Optional[str] = "100"
    lead_time_days: Optional[int] = Field(14, ge=0, description="Lead time in days must be non-negative")
    warranty: Optional[str] = "1 Year"
    payment_terms: Optional[str] = "Net 30"
    validity_period: Optional[str] = "30 days"
    status: Optional[str] = "received"
    notes: Optional[str] = None

class QuotationResponse(BaseModel):
    id: str
    rfq_id: Optional[str] = None
    requirement_id: Optional[str] = None
    supplier_id: str
    supplier_name: Optional[str] = None
    rfq_dispatch_id: Optional[str] = None
    quote_reference: Optional[str] = None
    status: Optional[str] = "received"
    extracted_data: Dict[str, Any]
    extraction_confidence: float
    received_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class RecommendationResponse(BaseModel):
    id: str
    requirement_id: str
    summary: str
    recommended_supplier_id: Optional[str] = None
    awarded_supplier_id: Optional[str] = None
    awarded_supplier_name: Optional[str] = None
    awarded_at: Optional[datetime] = None
    award_notes: Optional[str] = None
    comparison_matrix: Dict[str, Dict[str, Any]]
    generated_at: datetime

    class Config:
        from_attributes = True

class AwardRequest(BaseModel):
    supplier_id: str
    notes: Optional[str] = None
