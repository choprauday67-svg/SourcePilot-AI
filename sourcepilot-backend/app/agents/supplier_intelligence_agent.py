from typing import List, Dict, Any
from app.agents.base_agent import BaseAgent
from app.infrastructure.search_connectors.base import RawSupplierCandidate


class SupplierIntelligenceAgent(BaseAgent):
    """
    Agent 3: Enrich candidates with trust scores, risk flags, and verification signals.
    Phase 2 — Trust Score v1.5: multi-connector provenance weighting.
    """

    # Connector-specific trust bonuses (additive on top of base rating signal)
    CONNECTOR_TRUST_BONUSES: Dict[str, float] = {
        "trade_registry": 10.0,   # Government/compliance registry verified
        "review_sites": 6.0,       # High buyer review count & positive sentiment
        "marketplace": 3.0,        # Marketplace-verified badge (e.g., Gold Supplier)
        "web_search": 0.0,         # Baseline web search — no verification premium
        "serper_web_search": 0.0,
        "tavily_web_search": 0.0,
        "mock_web_search": 0.0,
    }

    # Category-specific risk signals (patterns that indicate elevated risk)
    HIGH_RISK_CATEGORIES = {"chemicals", "pharmaceuticals", "medical", "defence"}

    async def execute(self, candidate: RawSupplierCandidate) -> Dict[str, Any]:
        # --- Base trust from star rating (normalised to 0-100) ---
        base_trust = candidate.rating * 18.0  # e.g. 4.5 * 18 = 81

        # --- Certification bonuses ---
        cert_str = " ".join(c.upper() for c in candidate.certifications)
        if "ISO 9001" in cert_str:
            base_trust += 5.0
        if "ISO 14001" in cert_str:
            base_trust += 3.0
        if "CE" in cert_str or "ROHS" in cert_str:
            base_trust += 2.0
        if "D-U-N-S" in cert_str or "SGS" in cert_str:
            base_trust += 4.0

        # --- Connector provenance premium (Phase 2) ---
        connector_bonus = self.CONNECTOR_TRUST_BONUSES.get(
            candidate.source_connector, 0.0
        )
        base_trust += connector_bonus

        # --- Review-site sentiment bonus (Phase 2) ---
        sentiment_score = candidate.raw_metadata.get("sentiment_score", None)
        if sentiment_score is not None:
            if sentiment_score >= 0.9:
                base_trust += 5.0
            elif sentiment_score >= 0.8:
                base_trust += 3.0

        # --- Registry verified bonus (Phase 2) ---
        if candidate.raw_metadata.get("registry_verified", False):
            base_trust += 5.0
        if candidate.raw_metadata.get("marketplace_verified", False):
            base_trust += 2.0

        trust_score = min(99.0, max(55.0, round(base_trust, 1)))

        # --- Risk flag analysis ---
        risk_flags: List[str] = []
        if trust_score < 70.0:
            risk_flags.append("Limited historical verification data")
        if not candidate.contact_email:
            risk_flags.append("Primary sales contact email unverified")
        if candidate.rating < 4.0:
            risk_flags.append("Below-average buyer rating (< 4.0 stars)")
        if candidate.connector_source_label() in {"web_search", "mock_web_search"} and trust_score < 80.0:
            risk_flags.append("Sourced from web search only — no registry/marketplace verification")
        review_count = candidate.raw_metadata.get("review_count", None)
        if review_count is not None and review_count < 10:
            risk_flags.append("Fewer than 10 buyer reviews — limited public sentiment data")

        # --- Reviews summary ---
        review_snippet = candidate.raw_metadata.get("top_review", "")
        reviews_summary = (
            review_snippet
            if review_snippet
            else f"Verified B2B supplier discovered via {candidate.source_connector}. "
            f"Trust Score {trust_score}/100 based on multi-source signals."
        )

        return {
            "trust_score": trust_score,
            "risk_flags": risk_flags,
            "reviews_summary": reviews_summary,
            "certifications": candidate.certifications,
            "source_connector": candidate.source_connector,
            "connector_bonus_applied": connector_bonus,
        }
