from typing import List, Dict, Any, Tuple
from app.agents.base_agent import BaseAgent
from app.schemas.agent_io_schemas import (
    RequirementExtractionOutput,
    SupplierRankingOutput,
    SupplierRankItem,
)


class SupplierRankingAgent(BaseAgent):
    """
    Agent 4: Rank suppliers using explainable weighted criteria.
    Phase 2 — Category-aware weighting matrices + multi-connector provenance signals.
    """

    # Category-specific factor weights (must sum to 1.0)
    # Keys: trust_weight, cert_weight, lead_time_weight, price_weight, review_weight
    CATEGORY_WEIGHTS: Dict[str, Dict[str, float]] = {
        "electronics": {
            "trust": 0.30, "certification": 0.20, "lead_time": 0.25,
            "price": 0.15, "review": 0.10,
        },
        "machinery": {
            "trust": 0.30, "certification": 0.25, "lead_time": 0.20,
            "price": 0.15, "review": 0.10,
        },
        "chemicals": {
            "trust": 0.20, "certification": 0.40, "lead_time": 0.15,
            "price": 0.10, "review": 0.15,
        },
        "construction": {
            "trust": 0.25, "certification": 0.25, "lead_time": 0.20,
            "price": 0.20, "review": 0.10,
        },
        "services": {
            "trust": 0.25, "certification": 0.10, "lead_time": 0.15,
            "price": 0.20, "review": 0.30,
        },
        "raw materials": {
            "trust": 0.25, "certification": 0.20, "lead_time": 0.25,
            "price": 0.25, "review": 0.05,
        },
        # Default weights applied when category is unrecognised
        "default": {
            "trust": 0.30, "certification": 0.20, "lead_time": 0.20,
            "price": 0.20, "review": 0.10,
        },
    }

    # Multi-connector provenance bonus applied to final score
    CONNECTOR_RANK_BONUS: Dict[str, float] = {
        "trade_registry": 5.0,
        "review_sites": 3.0,
        "marketplace": 1.5,
        "web_search": 0.0,
        "serper_web_search": 0.0,
        "tavily_web_search": 0.0,
        "mock_web_search": 0.0,
    }

    def _resolve_weights(self, category: str) -> Dict[str, float]:
        """Return the weight matrix for this category (case-insensitive, partial match)."""
        cat = category.lower().strip()
        for key in self.CATEGORY_WEIGHTS:
            if key in cat or cat in key:
                return self.CATEGORY_WEIGHTS[key]
        return self.CATEGORY_WEIGHTS["default"]

    def _cert_score(
        self,
        must_haves: set,
        supplier_certs: List[str],
    ) -> Tuple[float, str]:
        """Return (normalised cert score 0-100, human-readable label)."""
        certs_upper = set(c.upper() for c in supplier_certs)
        if not must_haves:
            return (85.0, "No mandatory certifications specified")
        matched = must_haves & certs_upper
        ratio = len(matched) / len(must_haves)
        if ratio >= 1.0:
            label = f"Full Match ({', '.join(supplier_certs)})"
            return (100.0, label)
        elif ratio > 0:
            label = f"Partial Match ({len(matched)}/{len(must_haves)} certs verified)"
            return (60.0 + ratio * 30.0, label)
        else:
            return (30.0, "No required certifications confirmed")

    async def execute(
        self,
        requirement: RequirementExtractionOutput,
        supplier_records: List[Dict[str, Any]],
    ) -> SupplierRankingOutput:
        weights = self._resolve_weights(requirement.category)
        must_haves = set(c.upper() for c in requirement.must_have_certifications)
        rankings: List[SupplierRankItem] = []

        for item in supplier_records:
            supplier_id = item["id"]
            supplier_name = item["company_name"]
            profile = item.get("profile", {})

            trust_score = min(100.0, profile.get("trust_score", 85.0))
            certs = profile.get("certifications", [])
            source_connector = profile.get("source_connector", "web_search")

            # --- Factor scores (each 0-100) ---
            cert_score, cert_label = self._cert_score(must_haves, certs)

            # Lead time score — penalise long lead times relative to 30-day baseline
            # (we don't have exact lead time yet so use a tier from source connector)
            lead_time_tiers = {
                "trade_registry": 85.0,
                "marketplace": 75.0,
                "review_sites": 80.0,
            }
            lead_time_score = lead_time_tiers.get(source_connector, 70.0)

            # Price score — placeholder; will improve once quotations arrive
            price_score = 80.0

            # Review score from sentiment data
            review_count = item.get("raw_metadata_review_count", 0)
            sentiment = item.get("raw_metadata_sentiment", 0.0)
            if sentiment >= 0.9:
                review_score = 95.0
            elif sentiment >= 0.8:
                review_score = 80.0
            elif review_count > 50:
                review_score = 70.0
            else:
                review_score = 60.0

            # --- Weighted composite score ---
            composite = (
                weights["trust"] * trust_score
                + weights["certification"] * cert_score
                + weights["lead_time"] * lead_time_score
                + weights["price"] * price_score
                + weights["review"] * review_score
            )

            # --- Connector provenance bonus (Phase 2) ---
            provenance_bonus = self.CONNECTOR_RANK_BONUS.get(source_connector, 0.0)
            final_score = min(98.5, max(55.0, composite + provenance_bonus))

            explanation = {
                "summary": (
                    f"{supplier_name} scored {final_score:.1f}/100 under "
                    f"'{requirement.category}' category weighting. "
                    f"Trust baseline {trust_score}/100. "
                    f"Connector provenance: {source_connector} (+{provenance_bonus} pts)."
                ),
                "price_fit": "Competitive market alignment (pre-quote estimate)",
                "certification_match": cert_label,
                "lead_time": f"Estimated tier score {lead_time_score}/100",
                "trust_score": trust_score,
                "source_connector": source_connector,
                "provenance_bonus": provenance_bonus,
                "category_weights_applied": weights,
                "risk_analysis": profile.get("risk_analysis", {}),
                "risk_flags": profile.get("risk_flags", []),
                "score_components": {
                    "trust": round(weights["trust"] * trust_score, 2),
                    "certification": round(weights["certification"] * cert_score, 2),
                    "lead_time": round(weights["lead_time"] * lead_time_score, 2),
                    "price": round(weights["price"] * price_score, 2),
                    "review": round(weights["review"] * review_score, 2),
                    "provenance_bonus": provenance_bonus,
                },
            }

            rankings.append(
                SupplierRankItem(
                    supplier_id=supplier_id,
                    rank_score=round(final_score, 1),
                    rank_explanation=explanation,
                )
            )

        rankings.sort(key=lambda x: x.rank_score, reverse=True)
        return SupplierRankingOutput(rankings=rankings)
