from typing import Dict, List, Optional
from app.infrastructure.search_connectors.base import SupplierConnector
from app.infrastructure.search_connectors.web_search_connector import WebSearchConnector

class ConnectorRegistry:
    def __init__(self):
        self._connectors: Dict[str, SupplierConnector] = {}

    def register(self, connector: SupplierConnector) -> None:
        self._connectors[connector.name] = connector

    def get_connector(self, name: str) -> Optional[SupplierConnector]:
        return self._connectors.get(name)

    def get_all_connectors(self) -> List[SupplierConnector]:
        return list(self._connectors.values())

connector_registry = ConnectorRegistry()
connector_registry.register(WebSearchConnector())
