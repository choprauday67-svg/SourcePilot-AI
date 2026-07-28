from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel

class ManualQuotationCreate(BaseModel):
    requirement_id: str
    supplier_id: str
    unit_price: float
    total_price: float
    currency: str = "USD"
    moq: Optional[str] = "100"
    lead_time_days: Optional[int] = 14
    warranty: Optional[str] = "1 Year"
    payment_terms: Optional[str] = "Net 30"
    validity_period: Optional[str] = "30 days"
    notes: Optional[str] = None

class QuotationResponse(BaseModel):
    id: str
    requirement_id: str
    supplier_id: str
    rfq_dispatch_id: Optional[str] = None
    extracted_data: Dict[str, Any]
    extraction_confidence: float
    received_at: datetime

    class Config:
        from_attributes = True

class RecommendationResponse(BaseModel):
    id: str
    requirement_id: str
    summary: str
    recommended_supplier_id: Optional[str] = None
    comparison_matrix: Dict[str, Dict[str, Any]]
    generated_at: datetime

    class Config:
        from_attributes = True
