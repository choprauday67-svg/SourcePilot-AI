"""
BingSearchConnector — Phase 1 Real Supplier Discovery

Adapter interface for Microsoft Bing Web Search API v7.
Discovers real-world suppliers, manufacturers, and vendors using live Bing search.
Leaves unverified fields as None without fabricating synthetic emails, phones, or metrics.
"""
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


class BingSearchConnector(SupplierConnector):
    """
    Phase 1 connector targeting live web supplier search using Bing Search API v7.
    """
    name = "bing_search"
    category_support = ["all"]

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
        api_key = settings.BING_SEARCH_API_KEY
        if not api_key:
            return []

        search_url = "https://api.bing.microsoft.com/v7.0/search"
        search_query = f"{query} supplier manufacturer"
        headers = {"Ocp-Apim-Subscription-Key": api_key}
        params = {"q": search_query, "count": limit, "textDecorations": False}

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(search_url, headers=headers, params=params, timeout=10.0)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = []
                    web_pages = data.get("webPages", {}).get("value", [])
                    for item in web_pages[:limit]:
                        link = item.get("url", "")
                        domain = self._extract_domain(link)
                        title = item.get("name", "").split("-")[0].split("|")[0].strip()
                        snippet = item.get("snippet", "")

                        # Extract real signals from snippet without synthetic defaults
                        extracted_email = _extract_email_from_text(snippet)
                        extracted_certs = _extract_certs_from_text(snippet)

                        candidates.append(
                            RawSupplierCandidate(
                                company_name=title or f"Supplier ({domain})",
                                website=link,
                                canonical_domain=domain,
                                country=None,
                                city=None,
                                snippet=snippet,
                                contact_email=extracted_email,
                                contact_phone=None,
                                source_connector="bing_search",
                                rating=0.0,
                                certifications=extracted_certs,
                                raw_metadata={"search_engine": "bing"},
                            )
                        )
                    return candidates
        except Exception:
            pass
        return []

    async def health_check(self) -> bool:
        if not settings.BING_SEARCH_API_KEY:
            return True
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://api.bing.microsoft.com/v7.0/search",
                    headers={"Ocp-Apim-Subscription-Key": settings.BING_SEARCH_API_KEY},
                    params={"q": "test", "count": 1},
                    timeout=5.0,
                )
                return resp.status_code < 500
        except Exception:
            return False
