from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class BudgetRange(BaseModel):
    min: Optional[float] = None
    max: Optional[float] = None
    currency: str = "USD"

class RequirementExtractionOutput(BaseModel):
    product: str = Field(description="Main product or service name being requested")
    category: str = Field(description="Procurement category (e.g. Electronics, Machinery, Chemicals, Construction)")
    quantity: float = Field(description="Numeric quantity required")
    unit: str = Field(description="Unit of measurement e.g. units, kg, meters, hours")
    specifications: List[str] = Field(default_factory=list, description="Technical specs or requirements")
    budget_range: Optional[BudgetRange] = Field(default=None, description="Estimated budget min/max and currency")
    delivery_location: Optional[str] = Field(default=None, description="Target destination city/state/country")
    timeline: Optional[str] = Field(default=None, description="Requested delivery deadline or lead time")
    must_have_certifications: List[str] = Field(default_factory=list, description="Mandatory certifications e.g. ISO 9001")

class RankExplanationFactor(BaseModel):
    price_fit: str
    certification_match: str
    lead_time: str
    trust_score: float

class SupplierRankItem(BaseModel):
    supplier_id: str
    rank_score: float = Field(description="Overall match score out of 100")
    rank_explanation: Dict[str, Any] = Field(description="Explainable breakdown of score factors")

class SupplierRankingOutput(BaseModel):
    rankings: List[SupplierRankItem]

class RFQGenerationOutput(BaseModel):
    title: str
    sections: Dict[str, str] = Field(description="Dict of section header -> markdown content")
    formatted_rfq_markdown: str

class QuotationExtractionOutput(BaseModel):
    unit_price: float
    total_price: float
    currency: str = "USD"
    moq: Optional[str] = None
    lead_time_days: Optional[int] = None
    validity_period: Optional[str] = "30 days"
    payment_terms: Optional[str] = "Net 30"
    notes: Optional[str] = None
    confidence_score: float = 1.0

class RecommendationOutput(BaseModel):
    summary: str = Field(description="Executive summary rationale for recommendation")
    recommended_supplier_id: Optional[str] = None
    comparison_matrix: Dict[str, Dict[str, Any]] = Field(description="Side-by-side metric comparison")
