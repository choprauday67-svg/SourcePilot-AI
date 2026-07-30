"""
Phase 3 — Price Trend Analytics Routes

Endpoints for historical quotation price analysis, price movement trajectories,
category benchmarks, and supplier performance scorecards.
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.infrastructure.db.base import get_db
from app.infrastructure.db.models.quotation import Quotation
from app.infrastructure.db.models.requirement import ProcurementRequirement
from app.infrastructure.db.models.recommendation import Recommendation
from app.infrastructure.db.models.supplier import Supplier
from app.infrastructure.db.models.user import User
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/analytics", tags=["Price Analytics"])


@router.get("/price-trends", response_model=Dict[str, Any])
def get_price_trends(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get historical quotation price trends, category price benchmarks,
    and lead time averages across canonical unique quotations.
    """
    raw_quotes = (
        db.query(Quotation)
        .join(ProcurementRequirement, Quotation.requirement_id == ProcurementRequirement.id)
        .filter(ProcurementRequirement.organization_id == current_user.organization_id)
        .order_by(Quotation.received_at.desc())
        .all()
    )

    # Deduplicate raw quotes by (requirement_id, supplier_id) so metrics are canonical
    seen_keys = set()
    quotes = []
    for q in raw_quotes:
        key = (q.requirement_id, q.supplier_id)
        if key not in seen_keys:
            seen_keys.add(key)
            quotes.append(q)

    categories: Dict[str, List[float]] = {}
    supplier_perf: Dict[str, Dict[str, Any]] = {}
    time_series: List[Dict[str, Any]] = []

    for q in quotes:
        extracted = q.extracted_data or {}
        unit_price = extracted.get("unit_price") or extracted.get("total_price") or 0.0
        order_total = extracted.get("total_price") or 0.0
        lead_time = extracted.get("lead_time_days") or 14

        req = db.query(ProcurementRequirement).filter(ProcurementRequirement.id == q.requirement_id).first() if q.requirement_id else None
        cat = (req.structured_data or {}).get("category", "Industrial") if req else "Industrial"

        categories.setdefault(cat, []).append(unit_price)

        sup = db.query(Supplier).filter(Supplier.id == q.supplier_id).first()
        sup_name = sup.company_name if sup else "Unknown Supplier"
        if sup_name not in supplier_perf:
            supplier_perf[sup_name] = {"name": sup_name, "quote_count": 0, "total_spend": 0.0, "avg_lead_time": 0.0}

        # Check if supplier was awarded for this requirement
        awarded_rec = db.query(Recommendation).filter(
            Recommendation.requirement_id == q.requirement_id,
            Recommendation.awarded_supplier_id == q.supplier_id
        ).first()

        # Supplier Total Spend uses awarded order total value (total_price)
        awarded_spend = order_total if awarded_rec else 0.0

        supplier_perf[sup_name]["quote_count"] += 1
        supplier_perf[sup_name]["total_spend"] += round(awarded_spend, 2)
        supplier_perf[sup_name]["avg_lead_time"] = round((supplier_perf[sup_name]["avg_lead_time"] + lead_time) / 2, 1)

        date_str = q.received_at.strftime("%Y-%m") if q.received_at else "2026-07"
        time_series.append({
            "date": date_str,
            "category": cat,
            "supplier": sup_name,
            "unit_price": unit_price,
            "lead_time_days": lead_time,
        })

    category_summary = []
    for cat_name, prices in categories.items():
        if prices:
            category_summary.append({
                "category": cat_name,
                "avg_price": round(sum(prices) / len(prices), 2),
                "min_price": round(min(prices), 2),
                "max_price": round(max(prices), 2),
                "quote_count": len(prices),
            })

    return {
        "total_quotations_analyzed": len(quotes),
        "category_summary": category_summary,
        "supplier_performance": list(supplier_perf.values()),
        "time_series": time_series,
    }
