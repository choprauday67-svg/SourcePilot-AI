from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.infrastructure.db.base import get_db
from app.infrastructure.db.models.requirement import ProcurementRequirement
from app.infrastructure.db.models.supplier import Supplier
from app.infrastructure.db.models.quotation import Quotation
from app.infrastructure.db.models.recommendation import Recommendation
from app.infrastructure.db.models.user import User
from app.schemas.quotation_schemas import ManualQuotationCreate, QuotationResponse, RecommendationResponse
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
    return quote

@router.get("/requirement/{requirement_id}", response_model=List[QuotationResponse])
def get_quotations_for_requirement(
    requirement_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(Quotation)\
        .join(ProcurementRequirement)\
        .filter(Quotation.requirement_id == requirement_id, ProcurementRequirement.organization_id == current_user.organization_id)\
        .all()

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

    quotes = db.query(Quotation).filter(Quotation.requirement_id == requirement_id).all()
    
    quotes_payload = []
    for q in quotes:
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

    # Upsert recommendation record
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

    db.commit()
    db.refresh(rec)
    return rec
