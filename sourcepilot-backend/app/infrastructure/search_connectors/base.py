from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class RawSupplierCandidate:
    company_name: str
    website: str
    canonical_domain: str
    country: Optional[str] = "United States"
    city: Optional[str] = "San Francisco"
    snippet: str = ""
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    source_connector: str = "web_search"
    rating: float = 4.5
    certifications: List[str] = field(default_factory=lambda: ["ISO 9001"])
    estimated_price_range: Optional[Dict[str, Any]] = None
    raw_metadata: Dict[str, Any] = field(default_factory=dict)

    def connector_source_label(self) -> str:
        """Return a normalised source label for provenance classification."""
        return self.source_connector.lower().replace("-", "_")


class SupplierConnector(ABC):
    name: str
    category_support: List[str]

    @abstractmethod
    async def search(self, query: str, category: Optional[str] = None, limit: int = 5) -> List[RawSupplierCandidate]:
        """Search for suppliers matching a query/category."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the external API/service is reachable."""
        pass
