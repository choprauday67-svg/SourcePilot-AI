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


class MarketIntelligenceOutput(BaseModel):
    # Phase 3 primary fields (used by frontend & tests)
    intelligence_source: str = Field(
        default="simulated_agent_intelligence",
        description="Source of intelligence e.g. live_connector_intelligence or simulated_agent_intelligence",
    )
    market_sentiment: str = Field(
        default="stable",
        description="One of: bullish, bearish, stable, volatile",
    )
    analysis_summary: str = Field(
        default="",
        description="Executive narrative of the current market state for this category",
    )
    supply_chain_risks: List[str] = Field(
        default_factory=list,
        description="Bulleted list of identified supply chain risk factors",
    )
    key_opportunities: List[str] = Field(
        default_factory=list,
        description="Bulleted list of procurement opportunities or favourable conditions",
    )
    recommended_actions: List[str] = Field(
        default_factory=list,
        description="Ordered list of recommended procurement actions",
    )
    recommended_purchase_timing: str = Field(
        default="",
        description="Human-readable timing recommendation, e.g. 'Buy within 14 days'",
    )
    price_forecast_90_days: str = Field(
        default="",
        description="Narrative price forecast over the next 90 days",
    )
    # Legacy fields retained for backward compatibility
    market_trend_summary: str = Field(default="", description="Legacy: executive market summary")
    price_movement_forecast: str = Field(default="", description="Legacy: price movement forecast")
    supplier_responsiveness_index: float = Field(default=85.0, description="0-100 score")
    recommended_sourcing_strategy: str = Field(default="", description="Legacy: sourcing strategy")
    best_buy_window: str = Field(default="", description="Legacy: optimal buy window")
    category_insights: List[Dict[str, Any]] = Field(default_factory=list, description="Per-category insights")

