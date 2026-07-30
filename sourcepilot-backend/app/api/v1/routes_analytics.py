from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.infrastructure.db.base import get_db
from app.infrastructure.db.models.requirement import ProcurementRequirement
from app.infrastructure.db.models.quotation import Quotation
from app.infrastructure.db.models.recommendation import Recommendation
from app.infrastructure.db.models.user import User
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/summary")
def get_analytics_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    total_reqs = db.query(ProcurementRequirement)\
        .filter(ProcurementRequirement.organization_id == current_user.organization_id)\
        .count()

    completed_reqs = db.query(ProcurementRequirement)\
        .filter(
            ProcurementRequirement.organization_id == current_user.organization_id,
            ProcurementRequirement.status.in_(["quoted", "completed", "rfq_sent", "awarded"])
        )\
        .count()

    # Total Procured Spend: count actual awarded/procured contract value only
    awarded_recs = (
        db.query(Recommendation)
        .join(ProcurementRequirement, Recommendation.requirement_id == ProcurementRequirement.id)
        .filter(
            ProcurementRequirement.organization_id == current_user.organization_id,
            Recommendation.awarded_supplier_id.isnot(None)
        )
        .all()
    )

    total_procured_spend = 0.0
    cat_spends = {}

    for rec in awarded_recs:
        win_quote = (
            db.query(Quotation)
            .filter(
                Quotation.requirement_id == rec.requirement_id,
                Quotation.supplier_id == rec.awarded_supplier_id
            )
            .order_by(Quotation.received_at.desc())
            .first()
        )
        if win_quote:
            order_total = (win_quote.extracted_data or {}).get("total_price", 0.0)
            total_procured_spend += order_total

            req = db.query(ProcurementRequirement).filter(ProcurementRequirement.id == rec.requirement_id).first()
            cat = (req.category if req and req.category else ((req.structured_data or {}).get("category") if req else "General")) or "General"
            cat_spends[cat] = cat_spends.get(cat, 0.0) + order_total

    spend_by_category = [{"category": k, "spend": round(v, 2)} for k, v in cat_spends.items()]

    # Dynamic average cycle time in hours
    reqs = db.query(ProcurementRequirement)\
        .filter(ProcurementRequirement.organization_id == current_user.organization_id)\
        .all()
    
    cycle_hours = []
    for r in reqs:
        if r.updated_at and r.created_at and r.updated_at > r.created_at:
            hrs = (r.updated_at - r.created_at).total_seconds() / 3600.0
            if hrs > 0:
                cycle_hours.append(hrs)
    
    avg_cycle_time = round(sum(cycle_hours) / len(cycle_hours), 1) if cycle_hours else (1.2 if total_reqs > 0 else 0.0)

    return {
        "total_requirements": total_reqs,
        "active_sourcing": max(0, total_reqs - completed_reqs),
        "completed_requirements": completed_reqs,
        "total_procurement_spend": round(total_procured_spend, 2),
        "average_cycle_time_hours": avg_cycle_time,
        "spend_by_category": spend_by_category,
    }


@router.get("/market-intelligence")
async def get_market_intelligence(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Execute Agent 9 (MarketIntelligenceAgent) over canonical unique quotes in organization."""
    from app.agents.orchestrator import orchestrator
    raw_quotes = (
        db.query(Quotation)
        .join(ProcurementRequirement, Quotation.requirement_id == ProcurementRequirement.id)
        .filter(ProcurementRequirement.organization_id == current_user.organization_id)
        .order_by(Quotation.received_at.desc())
        .all()
    )

    seen = set()
    quote_records = []
    for q in raw_quotes:
        key = (q.requirement_id, q.supplier_id)
        if key in seen:
            continue
        seen.add(key)
        quote_records.append({
            "id": q.id,
            "data": q.extracted_data,
            "received_at": str(q.received_at),
        })

    return await orchestrator.market_intelligence_agent.execute(quote_records)


@router.get("/market-intelligence/{requirement_id}")
async def get_market_intelligence_for_requirement(
    requirement_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Phase 3 — Execute Market Intelligence Agent for a specific requirement.
    Uses canonical unique quotation dataset across the organization (same data source as Spend Analytics & Price Trends).
    """
    from app.agents.orchestrator import orchestrator

    req = db.query(ProcurementRequirement).filter(
        ProcurementRequirement.id == requirement_id,
        ProcurementRequirement.organization_id == current_user.organization_id,
    ).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")

    # Gather canonical deduplicated quotes across organization (same data source as Spend Analytics & Price Trends)
    raw_quotes = (
        db.query(Quotation)
        .join(ProcurementRequirement, Quotation.requirement_id == ProcurementRequirement.id)
        .filter(ProcurementRequirement.organization_id == current_user.organization_id)
        .order_by(Quotation.received_at.desc())
        .all()
    )

    seen = set()
    quote_records = []
    for q in raw_quotes:
        key = (q.requirement_id, q.supplier_id)
        if key in seen:
            continue
        seen.add(key)
        quote_records.append({
            "id": q.id,
            "data": q.extracted_data,
            "received_at": str(q.received_at),
            "requirement_context": req.structured_data or {},
        })

    return await orchestrator.market_intelligence_agent.execute(
        quote_records,
        requirement_context=req.structured_data or {},
    )
