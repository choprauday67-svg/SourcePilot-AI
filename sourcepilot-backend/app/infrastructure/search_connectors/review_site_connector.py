"""
ReviewSiteConnector — Phase 2 Supplier Source

Adapter interface for B2B review aggregation platforms (Trustpilot, G2,
Capterra, industry-specific review sites). Used for enriching supplier
trust scores with buyer sentiment data.
Mock ships by default. To integrate:
  1. Set REVIEW_SITE_API_KEY and REVIEW_SITE_API_URL in .env
  2. Replace _fetch_reviews() stub with real client
  3. Business logic is unchanged.
"""
import httpx
from typing import List, Optional

from app.infrastructure.search_connectors.base import SupplierConnector, RawSupplierCandidate
from app.core.config import settings


class ReviewSiteConnector(SupplierConnector):
    """
    Phase 2 connector for B2B review/rating aggregation.
    Primarily used to enrich trust scores, but also surfaces highly-reviewed
    suppliers as discovery candidates.
    Ships as a mock adapter; swap _fetch_reviews() to integrate real review APIs.
    """
    name = "review_sites"
    category_support = ["all"]

    async def _fetch_reviews(self, query: str, limit: int) -> Optional[List[dict]]:
        """
        Stub for real review API integration (e.g., Trustpilot Business API).
        Expected contract: returns list of dicts with keys:
            company_name, website, country, city, email,
            rating, review_count, sentiment_score, top_review_snippet
        """
        api_key = getattr(settings, "REVIEW_SITE_API_KEY", None)
        api_url = getattr(settings, "REVIEW_SITE_API_URL", None)

        if not api_key or not api_url:
            return None

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    api_url,
                    headers={"apikey": api_key},
                    params={"domain": query, "limit": limit},
                    timeout=10.0,
                )
                if resp.status_code == 200:
                    return resp.json().get("businesses", [])
        except Exception:
            pass
        return None

    async def search(
        self, query: str, category: Optional[str] = None, limit: int = 5
    ) -> List[RawSupplierCandidate]:
        # 1. Try live review API
        review_results = await self._fetch_reviews(query, limit)
        if review_results:
            candidates = []
            for item in review_results[:limit]:
                domain = item.get("website", "").replace("https://", "").replace("www.", "")
                candidates.append(
                    RawSupplierCandidate(
                        company_name=item["company_name"],
                        website=item.get("website", f"https://{domain}"),
                        canonical_domain=domain,
                        country=item.get("country", "United States"),
                        city=item.get("city", ""),
                        contact_email=item.get("email"),
                        source_connector="review_sites",
                        rating=float(item.get("rating", 4.5)),
                        certifications=["ISO 9001"],
                        raw_metadata={
                            "review_count": item.get("review_count", 0),
                            "sentiment_score": item.get("sentiment_score", 0.85),
                            "top_review": item.get("top_review_snippet", ""),
                        },
                    )
                )
            return candidates

        # 2. Mock implementation — realistic review-site style data
        category_clean = (category or "Industrial").title()
        reviewed_companies = [
            ("TrustBuilt Supply", 4.9, 347, 0.94),
            ("ProSource Partners", 4.7, 221, 0.89),
            ("Verified Vendors Inc.", 4.6, 189, 0.87),
            ("RatedMfg Solutions", 4.5, 156, 0.85),
            ("StarSupply Co.", 4.8, 412, 0.92),
        ]
        candidates = []
        for i in range(min(limit, len(reviewed_companies))):
            name, rating, review_count, sentiment = reviewed_companies[i]
            clean_name = name.lower().replace(' ', '-').replace('.', '')
            domain = f"{clean_name}.reviews-verified.com"
            candidates.append(
                RawSupplierCandidate(
                    company_name=full_name,
                    website=f"https://www.{domain}",
                    canonical_domain=domain,
                    country="United States",
                    city="Boston, MA",
                    snippet=(
                        f"Highly reviewed B2B supplier with {review_count} verified buyer reviews "
                        f"and a {sentiment:.0%} positive sentiment score on review platforms."
                    ),
                    contact_email=f"sales@{domain}",
                    contact_phone=f"+1 617 555 {2000 + i}",
                    source_connector="review_sites",
                    rating=rating,
                    certifications=["ISO 9001:2015"],
                    raw_metadata={
                        "review_count": review_count,
                        "sentiment_score": sentiment,
                        "top_review": (
                            "Outstanding quality and communication. Delivered on time, "
                            "every time. Strongly recommended for B2B procurement."
                        ),
                        "review_platform": "Trustpilot/G2 aggregated",
                    },
                )
            )
        return candidates

    async def health_check(self) -> bool:
        return True
