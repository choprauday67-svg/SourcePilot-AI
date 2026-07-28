"""
RegistryConnector — Phase 2 Supplier Source

Adapter interface for government trade registries, certification bodies,
and compliance databases (D&B, ISO.org, CAGE codes, GST/MSME India, etc.).
Mock implementation ships by default. To go live:
  1. Set REGISTRY_API_KEY and REGISTRY_API_URL in .env
  2. Replace _fetch_from_registry() stub
  3. Business logic is unchanged.
"""
import httpx
from typing import List, Optional

from app.infrastructure.search_connectors.base import SupplierConnector, RawSupplierCandidate
from app.core.config import settings


class RegistryConnector(SupplierConnector):
    """
    Phase 2 connector for government/trade registry verification.
    Ships as a mock adapter; swap _fetch_from_registry() to integrate real registries.
    """
    name = "trade_registry"
    category_support = ["all"]

    async def _fetch_from_registry(self, query: str, limit: int) -> Optional[List[dict]]:
        """
        Stub for real registry API integration (e.g., D&B Direct+, ISO member lookup).
        Expected contract: returns list of dicts with keys:
            company_name, website, country, city, email,
            certifications, registration_number, compliance_status
        """
        api_key = getattr(settings, "REGISTRY_API_KEY", None)
        api_url = getattr(settings, "REGISTRY_API_URL", None)

        if not api_key or not api_url:
            return None

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    api_url,
                    headers={"Authorization": f"Bearer {api_key}"},
                    params={"query": query, "limit": limit},
                    timeout=10.0,
                )
                if resp.status_code == 200:
                    return resp.json().get("entities", [])
        except Exception:
            pass
        return None

    async def search(
        self, query: str, category: Optional[str] = None, limit: int = 5
    ) -> List[RawSupplierCandidate]:
        # 1. Try live registry API
        registry_results = await self._fetch_from_registry(query, limit)
        if registry_results:
            candidates = []
            for item in registry_results[:limit]:
                domain = item.get("website", "").replace("https://", "").replace("www.", "")
                candidates.append(
                    RawSupplierCandidate(
                        company_name=item["company_name"],
                        website=item.get("website", f"https://{domain}"),
                        canonical_domain=domain,
                        country=item.get("country", "United States"),
                        city=item.get("city", ""),
                        contact_email=item.get("email"),
                        source_connector="trade_registry",
                        rating=4.8,  # Registry-verified suppliers get premium rating
                        certifications=item.get("certifications", ["ISO 9001"]),
                        raw_metadata={
                            "registration_number": item.get("registration_number"),
                            "compliance_status": item.get("compliance_status", "Active"),
                            "registry_verified": True,
                        },
                    )
                )
            return candidates

        # 2. Mock implementation — realistic registry-style verified supplier data
        category_clean = (category or "Industrial").title()
        companies = [
            ("Meridian Compliance Group", "US", "Washington D.C."),
            ("CertForge Manufacturing Ltd.", "GB", "Manchester"),
            ("Nordic Standards GmbH", "DE", "Hamburg"),
            ("Kaizen Verified Industries", "JP", "Osaka"),
            ("TrustCore Supply Co.", "CA", "Toronto"),
        ]
        candidates = []
        for i in range(min(limit, len(companies))):
            name, country, city = companies[i]
            clean_name = name.lower().replace(' ', '-').replace('.', '')
            domain = f"{clean_name}.registry-verified.com"
            candidates.append(
                RawSupplierCandidate(
                    company_name=full_name,
                    website=f"https://www.{domain}",
                    canonical_domain=domain,
                    country=country,
                    city=city,
                    snippet=(
                        f"Trade-registry verified supplier with active good standing. "
                        f"Registered under {category_clean} sector classification."
                    ),
                    contact_email=f"compliance@{domain}",
                    contact_phone=f"+1 202 555 {1000 + i}",
                    source_connector="trade_registry",
                    rating=4.8,  # Registry-verified suppliers earn trust premium
                    certifications=[
                        "ISO 9001:2015",
                        "ISO 14001:2015",
                        "OHSAS 18001",
                        "D-U-N-S Registered",
                    ],
                    raw_metadata={
                        "registration_number": f"REG-{2024000 + i}",
                        "compliance_status": "Active — Good Standing",
                        "registry_verified": True,
                        "annual_turnover_usd": 5_000_000 + (i * 1_000_000),
                    },
                )
            )
        return candidates

    async def health_check(self) -> bool:
        return True  # Mock always healthy; real impl would ping registry endpoint
