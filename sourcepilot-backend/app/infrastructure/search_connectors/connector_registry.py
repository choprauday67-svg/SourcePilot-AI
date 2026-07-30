from typing import Dict, List, Optional
from app.infrastructure.search_connectors.base import SupplierConnector
from app.infrastructure.search_connectors.web_search_connector import WebSearchConnector
from app.infrastructure.search_connectors.marketplace_connector import MarketplaceConnector
from app.infrastructure.search_connectors.registry_connector import RegistryConnector
from app.infrastructure.search_connectors.review_site_connector import ReviewSiteConnector
from app.infrastructure.search_connectors.bing_search_connector import BingSearchConnector


class ConnectorRegistry:
    def __init__(self):
        self._connectors: Dict[str, SupplierConnector] = {}

    def register(self, connector: SupplierConnector) -> None:
        self._connectors[connector.name] = connector

    def get_connector(self, name: str) -> Optional[SupplierConnector]:
        return self._connectors.get(name)

    def get_all_connectors(self) -> List[SupplierConnector]:
        return list(self._connectors.values())

    def list_connector_names(self) -> List[str]:
        return list(self._connectors.keys())


connector_registry = ConnectorRegistry()
connector_registry.register(WebSearchConnector())
connector_registry.register(MarketplaceConnector())
connector_registry.register(RegistryConnector())
connector_registry.register(ReviewSiteConnector())
connector_registry.register(BingSearchConnector())
