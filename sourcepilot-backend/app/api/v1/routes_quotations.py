from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.infrastructure.db.base import get_db
from app.infrastructure.db.models.requirement import ProcurementRequirement
from app.infrastructure.db.models.supplier import Supplier
from app.infrastructure.db.models.quotation import Quotation
from app.infrastructure.db.models.recommendation import Recommendation
from app.infrastructure.db.models.user import User
from app.schemas.quotation_schemas import (
    ManualQuotationCreate, QuotationResponse, RecommendationResponse, AwardRequest
)
from app.schemas.agent_io_schemas import RequirementExtractionOutput
from app.core.dependencies import get_current_user
from app.agents.orchestrator import orchestrator

router = APIRouter(prefix="/quotations", tags=["Quotations & Recommendations"])

@router.post("/manual", response_model=QuotationResponse)
def submit_manual_quotation(
    req: ManualQuotationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_req = db.query(ProcurementRequirement)\
        .filter(ProcurementRequirement.id == req.requirement_id, ProcurementRequirement.organization_id == current_user.organization_id)\
        .first()
    if not db_req:
        raise HTTPException(status_code=404, detail="Requirement not found")

    extracted_data = {
        "unit_price": req.unit_price,
        "total_price": req.total_price,
        "currency": req.currency,
        "moq": req.moq,
        "lead_time_days": req.lead_time_days,
        "warranty": req.warranty,
        "payment_terms": req.payment_terms,
        "validity_period": req.validity_period,
        "notes": req.notes
    }

    # Deduplicate: upsert quotation per (requirement_id, supplier_id)
    existing_quote = db.query(Quotation).filter(
        Quotation.requirement_id == req.requirement_id,
        Quotation.supplier_id == req.supplier_id
    ).first()

    if existing_quote:
        existing_quote.extracted_data = extracted_data
        existing_quote.extraction_confidence = 1.0
        existing_quote.received_at = datetime.utcnow()
        quote = existing_quote
    else:
        quote = Quotation(
            requirement_id=req.requirement_id,
            supplier_id=req.supplier_id,
            extracted_data=extracted_data,
            extraction_confidence=1.0
        )
        db.add(quote)

    db_req.status = "quoted"
    db.commit()
    db.refresh(quote)

    sup = db.query(Supplier).filter(Supplier.id == quote.supplier_id).first()
    res = QuotationResponse.model_validate(quote)
    res.supplier_name = sup.company_name if sup else "Supplier"
    return res

@router.get("/requirement/{requirement_id}", response_model=List[QuotationResponse])
def get_quotations_for_requirement(
    requirement_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Return one quotation per supplier (latest received_at) to prevent duplicate display
    quotes = db.query(Quotation)\
        .join(ProcurementRequirement)\
        .filter(Quotation.requirement_id == requirement_id, ProcurementRequirement.organization_id == current_user.organization_id)\
        .order_by(Quotation.received_at.desc())\
        .all()

    # Deduplicate by supplier_id — keep first (most recent) per supplier
    seen_suppliers: set = set()
    result = []
    for q in quotes:
        if q.supplier_id in seen_suppliers:
            continue
        seen_suppliers.add(q.supplier_id)
        sup = db.query(Supplier).filter(Supplier.id == q.supplier_id).first()
        res = QuotationResponse.model_validate(q)
        res.supplier_name = sup.company_name if sup else "Supplier"
        result.append(res)
    return result

@router.get("/recommendation/{requirement_id}", response_model=RecommendationResponse)
async def get_or_generate_recommendation(
    requirement_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_req = db.query(ProcurementRequirement)\
        .filter(ProcurementRequirement.id == requirement_id, ProcurementRequirement.organization_id == current_user.organization_id)\
        .first()
    if not db_req:
        raise HTTPException(status_code=404, detail="Requirement not found")

    # Deduplicated quotes list
    quotes_raw = db.query(Quotation).filter(Quotation.requirement_id == requirement_id)\
        .order_by(Quotation.received_at.desc()).all()

    seen: set = set()
    quotes_payload = []
    for q in quotes_raw:
        if q.supplier_id in seen:
            continue
        seen.add(q.supplier_id)
        sup = db.query(Supplier).filter(Supplier.id == q.supplier_id).first()
        quotes_payload.append({
            "supplier_id": q.supplier_id,
            "company_name": sup.company_name if sup else "Supplier",
            "extracted_data": q.extracted_data,
            "extraction_confidence": q.extraction_confidence
        })

    struct_data = RequirementExtractionOutput.model_validate(db_req.structured_data or {})
    
    # Run Recommendation Agent
    rec_out = await orchestrator.recommendation_agent.execute(struct_data, quotes_payload)

    # Upsert recommendation record (preserve award fields if already awarded)
    rec = db.query(Recommendation).filter(Recommendation.requirement_id == requirement_id).first()
    if not rec:
        rec = Recommendation(
            requirement_id=requirement_id,
            summary=rec_out.summary,
            recommended_supplier_id=rec_out.recommended_supplier_id,
            comparison_matrix=rec_out.comparison_matrix
        )
        db.add(rec)
    else:
        rec.summary = rec_out.summary
        rec.recommended_supplier_id = rec_out.recommended_supplier_id
        rec.comparison_matrix = rec_out.comparison_matrix
        # Do NOT overwrite awarded_supplier_id if already set

    db.commit()
    db.refresh(rec)

    # Enrich with awarded supplier name
    result = RecommendationResponse.model_validate(rec)
    if rec.awarded_supplier_id:
        awarded_sup = db.query(Supplier).filter(Supplier.id == rec.awarded_supplier_id).first()
        result.awarded_supplier_name = awarded_sup.company_name if awarded_sup else None
    return result


@router.post("/award/{requirement_id}", response_model=RecommendationResponse)
def award_supplier(
    requirement_id: str,
    payload: AwardRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Human-in-the-loop final supplier award. Persists the awarded supplier and marks requirement as awarded."""
    db_req = db.query(ProcurementRequirement)\
        .filter(ProcurementRequirement.id == requirement_id, ProcurementRequirement.organization_id == current_user.organization_id)\
        .first()
    if not db_req:
        raise HTTPException(status_code=404, detail="Requirement not found")

    supplier = db.query(Supplier).filter(Supplier.id == payload.supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    rec = db.query(Recommendation).filter(Recommendation.requirement_id == requirement_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="No recommendation found for this requirement. Generate a recommendation first.")

    if rec.awarded_supplier_id:
        raise HTTPException(
            status_code=400,
            detail=f"Supplier already awarded: {rec.awarded_supplier_id}. Award cannot be changed once set."
        )

    rec.awarded_supplier_id = payload.supplier_id
    rec.awarded_at = datetime.utcnow()
    rec.awarded_by_user_id = current_user.id
    rec.award_notes = payload.notes or ""

    db_req.status = "awarded"
    db.commit()
    db.refresh(rec)

    result = RecommendationResponse.model_validate(rec)
    result.awarded_supplier_name = supplier.company_name
    return result
