from typing import List, Optional
from app.agents.base_agent import BaseAgent
from app.schemas.agent_io_schemas import RequirementExtractionOutput
from app.infrastructure.search_connectors.connector_registry import connector_registry
from app.infrastructure.search_connectors.base import RawSupplierCandidate

class SupplierDiscoveryAgent(BaseAgent):
    """Agent 2: Query search connectors to discover candidate suppliers."""

    async def execute(self, structured_req: RequirementExtractionOutput, limit: int = 5) -> List[RawSupplierCandidate]:
        query = f"{structured_req.product} {structured_req.category}"
        connectors = connector_registry.get_all_connectors()
        
        all_candidates: List[RawSupplierCandidate] = []
        for connector in connectors:
            try:
                results = await connector.search(query=query, category=structured_req.category, limit=limit)
                all_candidates.extend(results)
            except Exception:
                continue

        # Deduplicate candidates by canonical_domain
        seen_domains = set()
        unique_candidates = []
        for candidate in all_candidates:
            if candidate.canonical_domain not in seen_domains:
                seen_domains.add(candidate.canonical_domain)
                unique_candidates.append(candidate)

        return unique_candidates[:limit]
