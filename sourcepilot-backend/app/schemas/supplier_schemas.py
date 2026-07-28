from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel

class SupplierContactResponse(BaseModel):
    id: str
    email: str
    phone: Optional[str] = None
    contact_name: Optional[str] = None
    is_primary: bool

    class Config:
        from_attributes = True

class SupplierProfileResponse(BaseModel):
    rating: float
    certifications: List[str]
    moq: Optional[str] = None
    warranty_terms: Optional[str] = None
    lead_time_days: Optional[float] = None
    trust_score: float
    risk_flags: List[str]

    class Config:
        from_attributes = True

class SupplierResponse(BaseModel):
    id: str
    company_name: str
    website: Optional[str] = None
    canonical_domain: Optional[str] = None
    location_country: Optional[str] = None
    location_city: Optional[str] = None
    contacts: List[SupplierContactResponse] = []
    profiles: List[SupplierProfileResponse] = []

    class Config:
        from_attributes = True

class SupplierRankedMatchResponse(BaseModel):
    match_id: str
    supplier: SupplierResponse
    rank_score: float
    rank_explanation: Dict[str, Any]
    selected_by_user: bool

class SupplierSelectionRequest(BaseModel):
    supplier_ids: List[str]
