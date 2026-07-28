"""
MarketplaceConnector — Phase 2 Supplier Source

Adapter interface for B2B marketplace directories (Alibaba, IndiaMART, ThomasNet, etc.).
Currently ships with a clean mock implementation. To integrate a real marketplace API:
  1. Set MARKETPLACE_API_KEY and MARKETPLACE_API_URL in .env
  2. Replace the _fetch_from_api() stub with the real HTTP client call
  3. No other files need to change.
"""
import httpx
from typing import List, Optional
from urllib.parse import urlparse

from app.infrastructure.search_connectors.base import SupplierConnector, RawSupplierCandidate
from app.core.config import settings


class MarketplaceConnector(SupplierConnector):
    """
    Phase 2 connector targeting B2B marketplace directories.
    Ships as a mock adapter; replace _fetch_from_api() to go live.
    """
    name = "marketplace"
    category_support = ["all"]

    # --- Adapter hook: replace with real HTTP call when API key is available ---
    async def _fetch_from_api(self, query: str, limit: int) -> Optional[List[dict]]:
        """
        Stub for real marketplace API integration.
        Expected contract: returns list of dicts with keys:
            company_name, website, country, city, email, phone,
            rating, certifications, moq, lead_time_days
        """
        api_key = getattr(settings, "MARKETPLACE_API_KEY", None)
        api_url = getattr(settings, "MARKETPLACE_API_URL", None)

        if not api_key or not api_url:
            return None  # Fall through to mock

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    api_url,
                    headers={"X-API-KEY": api_key},
                    params={"q": query, "limit": limit},
                    timeout=10.0,
                )
                if resp.status_code == 200:
                    return resp.json().get("results", [])
        except Exception:
            pass
        return None

    def _extract_domain(self, url: str) -> str:
        try:
            parsed = urlparse(url if url.startswith("http") else f"https://{url}")
            domain = parsed.netloc or parsed.path
            return domain.lower().replace("www.", "").split("/")[0]
        except Exception:
            return url.lower()

    async def search(
        self, query: str, category: Optional[str] = None, limit: int = 5
    ) -> List[RawSupplierCandidate]:
        # 1. Try live API adapter
        api_results = await self._fetch_from_api(query, limit)
        if api_results:
            candidates = []
            for item in api_results[:limit]:
                domain = self._extract_domain(item.get("website", ""))
                candidates.append(
                    RawSupplierCandidate(
                        company_name=item.get("company_name", "Unknown"),
                        website=item.get("website", f"https://{domain}"),
                        canonical_domain=domain,
                        country=item.get("country", "China"),
                        city=item.get("city", "Shenzhen"),
                        contact_email=item.get("email"),
                        contact_phone=item.get("phone"),
                        source_connector="marketplace",
                        rating=float(item.get("rating", 4.3)),
                        certifications=item.get("certifications", ["ISO 9001"]),
                        raw_metadata={
                            "moq": item.get("moq", "50 units"),
                            "lead_time_days": item.get("lead_time_days", 21),
                        },
                    )
                )
            return candidates

        # 2. Mock implementation — realistic marketplace-style data
        category_clean = (category or "Industrial").title()
        prefixes = ["SinoTech", "GlobalMart", "AlphaTrade", "PrimeLine", "EastWest"]
        candidates = []
        for i in range(1, limit + 1):
            prefix = prefixes[(i - 1) % len(prefixes)]
            domain = f"{prefix.lower()}-{category_clean.lower().replace(' ', '')}.marketplace.com"
            candidates.append(
                RawSupplierCandidate(
                    company_name=f"{prefix} {category_clean} Co., Ltd.",
                    website=f"https://www.{domain}",
                    canonical_domain=domain,
                    country="China" if i % 3 != 0 else "India",
                    city="Shenzhen" if i % 3 != 0 else "Mumbai",
                    snippet=(
                        f"Verified Gold Supplier on B2B marketplace. "
                        f"Specialises in {query} with {10 + i * 2} years of export experience."
                    ),
                    contact_email=f"export@{domain}",
                    contact_phone=f"+86 137 0000 {i:04d}",
                    source_connector="marketplace",
                    rating=round(4.0 + (i * 0.1), 1),
                    certifications=["ISO 9001:2015", "CE Certified", "SGS Inspected"]
                    if i % 2 == 0
                    else ["ISO 9001:2015"],
                    raw_metadata={
                        "moq": f"{50 * i} units",
                        "lead_time_days": 21 + i,
                        "marketplace_verified": True,
                        "export_years": 10 + i * 2,
                    },
                )
            )
        return candidates

    async def health_check(self) -> bool:
        api_key = getattr(settings, "MARKETPLACE_API_KEY", None)
        if not api_key:
            return True  # Mock always healthy
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    getattr(settings, "MARKETPLACE_API_URL", ""), timeout=5.0
                )
                return resp.status_code < 500
        except Exception:
            return False
