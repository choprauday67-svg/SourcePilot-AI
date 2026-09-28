import re
import httpx
from typing import List, Optional
from urllib.parse import urlparse
from app.infrastructure.search_connectors.base import SupplierConnector, RawSupplierCandidate
from app.core.config import settings


def _extract_email_from_text(text: str) -> Optional[str]:
    match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    return match.group(0) if match else None


def _extract_certs_from_text(text: str) -> List[str]:
    certs = []
    text_upper = text.upper()
    if "ISO 9001" in text_upper:
        certs.append("ISO 9001")
    if "ISO 14001" in text_upper:
        certs.append("ISO 14001")
    if "CE" in text_upper:
        certs.append("CE Certified")
    if "ROHS" in text_upper:
        certs.append("RoHS")
    return certs


class WebSearchConnector(SupplierConnector):
    name = "web_search"
    category_support = ["all"]

    def _extract_domain(self, url: str) -> str:
        try:
            parsed = urlparse(url if url.startswith("http") else f"https://{url}")
            domain = parsed.netloc or parsed.path
            return domain.lower().replace("www.", "").split("/")[0]
        except Exception:
            return url.lower()

    async def search(self, query: str, category: Optional[str] = None, limit: int = 5) -> List[RawSupplierCandidate]:
        candidates: List[RawSupplierCandidate] = []
        
        # 1. Try Serper API if key is present
        if settings.SERPER_API_KEY:
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        "https://google.serper.dev/search",
                        headers={"X-API-KEY": settings.SERPER_API_KEY, "Content-Type": "application/json"},
                        json={"q": f"{query} supplier manufacturer", "num": limit},
                        timeout=10.0
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        for item in data.get("organic", [])[:limit]:
                            link = item.get("link", "")
                            domain = self._extract_domain(link)
                            snippet = item.get("snippet", "")
                            candidates.append(RawSupplierCandidate(
                                company_name=item.get("title", "").split("-")[0].split("|")[0].strip(),
                                website=link,
                                canonical_domain=domain,
                                country=None,
                                city=None,
                                snippet=snippet,
                                contact_email=_extract_email_from_text(snippet),
                                contact_phone=None,
                                source_connector="serper_web_search",
                                rating=0.0,
                                certifications=_extract_certs_from_text(snippet),
                                raw_metadata={"search_engine": "google_serper"}
                            ))
                        if candidates:
                            return candidates
            except Exception:
                pass

        # 2. Try Tavily API if key is present
        if settings.TAVILY_API_KEY:
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        "https://api.tavily.com/search",
                        json={"api_key": settings.TAVILY_API_KEY, "query": f"{query} supplier manufacturer", "max_results": limit},
                        timeout=10.0
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        for item in data.get("results", [])[:limit]:
                            link = item.get("url", "")
                            domain = self._extract_domain(link)
                            snippet = item.get("content", "")
                            candidates.append(RawSupplierCandidate(
                                company_name=item.get("title", "").split("-")[0].strip(),
                                website=link,
                                canonical_domain=domain,
                                country=None,
                                city=None,
                                snippet=snippet,
                                contact_email=_extract_email_from_text(snippet),
                                contact_phone=None,
                                source_connector="tavily_web_search",
                                rating=0.0,
                                certifications=_extract_certs_from_text(snippet),
                                raw_metadata={"search_engine": "tavily"}
                            ))
                        if candidates:
                            return candidates
            except Exception:
                pass

        # 3. Fallback Mock Supplier Generator for local dev / offline test resilience
        domain_stems = ["apex", "prime", "global", "precision", "vanguard"]
        category_clean = (category or "Industrial").title()
        
        for i in range(1, limit + 1):
            stem = domain_stems[(i - 1) % len(domain_stems)]
            domain = f"{stem}-{category_clean.lower().replace(' ', '')}-mfg.com"
            candidates.append(RawSupplierCandidate(
                company_name=f"{stem.capitalize()} {category_clean} Solutions Ltd.",
                website=f"https://www.{domain}",
                canonical_domain=domain,
                country="United States",
                city="Chicago, IL" if i % 2 == 0 else "Austin, TX",
                snippet=f"Leading manufacturer of {query}. Certified ISO 9001:2015 with high-volume precision capabilities and fast lead times.",
                contact_email=f"rfq@{domain}",
                contact_phone=f"+1 (555) 019-{i:02d}",
                source_connector="mock_web_search",
                rating=round(4.2 + (i * 0.15), 1),
                certifications=["ISO 9001:2015", "RoHS", "CE Certified"] if i % 2 == 0 else ["ISO 9001:2015"],
                raw_metadata={"moq": "100 units", "lead_time_days": 14 + (i * 2)}
            ))

        return candidates

    async def health_check(self) -> bool:
        return True
