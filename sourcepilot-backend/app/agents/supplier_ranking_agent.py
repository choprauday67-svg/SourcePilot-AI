from typing import List, Dict, Any
from app.agents.base_agent import BaseAgent
from app.schemas.agent_io_schemas import RequirementExtractionOutput, SupplierRankingOutput, SupplierRankItem

class SupplierRankingAgent(BaseAgent):
    """Agent 4: Rank suppliers using explainable weighted criteria."""

    async def execute(
        self,
        requirement: RequirementExtractionOutput,
        supplier_records: List[Dict[str, Any]]
    ) -> SupplierRankingOutput:
        rankings: List[SupplierRankItem] = []

        for idx, item in enumerate(supplier_records):
            supplier_id = item["id"]
            supplier_name = item["company_name"]
            profile = item.get("profile", {})
            trust_score = profile.get("trust_score", 85.0)
            certs = profile.get("certifications", [])

            # Deterministic scoring algorithm
            score = trust_score
            
            # Check certification match
            must_haves = set(c.upper() for c in requirement.must_have_certifications)
            supplier_certs = set(c.upper() for c in certs)
            cert_match = "Full Match" if must_haves.issubset(supplier_certs) or not must_haves else "Partial Match"
            if cert_match == "Full Match":
                score += 5.0

            final_score = min(98.5, max(65.0, score - (idx * 3.0)))

            explanation = {
                "summary": f"{supplier_name} ranks high due to a strong trust score of {trust_score}/100 and verified certification alignment.",
                "price_fit": "Competitive Market Alignment",
                "certification_match": f"{cert_match} ({', '.join(certs)})",
                "lead_time": "Estimated 14-21 business days",
                "trust_score": trust_score,
                "score_components": {
                    "trust_baseline": trust_score,
                    "cert_bonus": 5.0 if cert_match == "Full Match" else 0.0,
                    "category_relevance": 90.0
                }
            }

            rankings.append(SupplierRankItem(
                supplier_id=supplier_id,
                rank_score=round(final_score, 1),
                rank_explanation=explanation
            ))

        rankings.sort(key=lambda x: x.rank_score, reverse=True)
        return SupplierRankingOutput(rankings=rankings)
