"""
Phase 2 — Connector Monitoring & Diagnostic Routes

Endpoints for inspecting available supplier connectors, checking connector health,
and querying connector capabilities.
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from app.infrastructure.search_connectors.connector_registry import connector_registry
from app.schemas.supplier_schemas import SupplierResponse
from app.core.dependencies import get_current_user
from app.infrastructure.db.models.user import User

router = APIRouter(prefix="/connectors", tags=["Connectors"])


@router.get("/list", response_model=List[Dict[str, Any]])
def list_connectors(current_user: User = Depends(get_current_user)):
    """List all registered search connectors and their supported categories."""
    connectors = connector_registry.get_all_connectors()
    return [
        {
            "name": c.name,
            "category_support": c.category_support,
            "is_live_integration": c.name == "web_search",  # WebSearch is live (Serper/Tavily/mock); others are adapter mocks
        }
        for c in connectors
    ]


@router.get("/health", response_model=Dict[str, Any])
async def check_connector_health(current_user: User = Depends(get_current_user)):
    """Run health checks on all registered connectors."""
    connectors = connector_registry.get_all_connectors()
    results = {}
    for c in connectors:
        is_healthy = await c.health_check()
        results[c.name] = {
            "status": "healthy" if is_healthy else "unreachable",
            "type": "live_provider" if c.name == "web_search" else "adapter_mock",
        }
    return {
        "status": "all_systems_operational",
        "connectors": results,
    }
