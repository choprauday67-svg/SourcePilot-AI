from typing import List, Dict, Any
from app.agents.base_agent import BaseAgent
from app.infrastructure.search_connectors.base import RawSupplierCandidate

class SupplierIntelligenceAgent(BaseAgent):
    """Agent 3: Enrich candidates with trust scores, risk flags, and verification signals."""

    async def execute(self, candidate: RawSupplierCandidate) -> Dict[str, Any]:
        # Compute baseline trust score based on certifications & rating
        base_trust = candidate.rating * 18.0 # e.g. 4.5 * 18 = 81
        if "ISO 9001" in "".join(candidate.certifications):
            base_trust += 10.0
        
        trust_score = min(99.0, max(60.0, base_trust))
        
        risk_flags = []
        if trust_score < 75.0:
            risk_flags.append("Limited historical verification data")
        if not candidate.contact_email:
            risk_flags.append("Primary sales email unverified")

        return {
            "trust_score": round(trust_score, 1),
            "risk_flags": risk_flags,
            "reviews_summary": f"Verified B2B supplier specializing in {candidate.company_name} core domain.",
            "certifications": candidate.certifications
        }
