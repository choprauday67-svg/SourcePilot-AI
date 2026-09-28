from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
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
from app.core.config import settings
from app.agents.orchestrator import orchestrator

router = APIRouter(prefix="/quotations", tags=["Quotations & Recommendations"])


@router.post("/manual", response_model=QuotationResponse)
def submit_manual_quotation(
    req: ManualQuotationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    import uuid
    from app.infrastructure.db.models.rfq import RFQ

    # 1. Validate Supplier existence
    sup = db.query(Supplier).filter(Supplier.id == req.supplier_id).first()
    if not sup:
        raise HTTPException(status_code=404, detail="Supplier not found")

    # 2. Resolve requirement & RFQ associations
    req_id = req.requirement_id
    rfq_obj = None

    if req.rfq_id:
        rfq_obj = db.query(RFQ).filter(RFQ.id == req.rfq_id).first()
        if not rfq_obj:
            raise HTTPException(status_code=404, detail="RFQ not found")
        req_id = rfq_obj.requirement_id

    if not req_id:
        raise HTTPException(status_code=400, detail="Either requirement_id or rfq_id must be provided")

    db_req = db.query(ProcurementRequirement)\
        .filter(ProcurementRequirement.id == req_id, ProcurementRequirement.organization_id == current_user.organization_id)\
        .first()
    if not db_req:
        raise HTTPException(status_code=404, detail="Requirement not found or access denied")

    # 3. Numeric validation safeguards
    if req.unit_price <= 0:
        raise HTTPException(status_code=400, detail="Unit price must be greater than 0")
    if req.total_price <= 0:
        raise HTTPException(status_code=400, detail="Total price must be greater than 0")
    if req.lead_time_days is not None and req.lead_time_days < 0:
        raise HTTPException(status_code=400, detail="Lead time in days cannot be negative")

    quote_ref = req.quote_reference.strip() if req.quote_reference and req.quote_reference.strip() else f"QUOTE-{uuid.uuid4().hex[:6].upper()}"

    extracted_data = {
        "unit_price": req.unit_price,
        "total_price": req.total_price,
        "currency": req.currency,
        "moq": req.moq,
        "lead_time_days": req.lead_time_days,
        "warranty": req.warranty,
        "payment_terms": req.payment_terms,
        "validity_period": req.validity_period,
        "notes": req.notes,
        "quote_reference": quote_ref,
    }

    # Deduplicate: upsert quotation per (requirement_id, supplier_id)
    existing_quote = db.query(Quotation).filter(
        Quotation.requirement_id == req_id,
        Quotation.supplier_id == req.supplier_id
    ).first()

    if existing_quote:
        existing_quote.rfq_id = rfq_obj.id if rfq_obj else existing_quote.rfq_id
        existing_quote.quote_reference = quote_ref
        existing_quote.status = req.status or "received"
        existing_quote.extracted_data = extracted_data
        existing_quote.extraction_confidence = 1.0
        existing_quote.received_at = datetime.utcnow()
        quote = existing_quote
    else:
        quote = Quotation(
            requirement_id=req_id,
            rfq_id=rfq_obj.id if rfq_obj else None,
            supplier_id=req.supplier_id,
            quote_reference=quote_ref,
            status=req.status or "received",
            extracted_data=extracted_data,
            extraction_confidence=1.0
        )
        db.add(quote)

    db_req.status = "quoted"
    db.commit()
    db.refresh(quote)

    res = QuotationResponse.model_validate(quote)
    res.supplier_name = sup.company_name
    return res


@router.post("/upload-attachment", response_model=QuotationResponse)
async def upload_quotation_attachment(
    requirement_id: str = Form(...),
    supplier_id: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Manually upload a supplier quotation attachment (PDF/XLSX/CSV/TXT), validate file size and extension,
    extract structured quotation fields via QuotationExtractionAgent, link to requirement + supplier, and upsert.
    """
    # 1. Validate requirement exists and belongs to current user's org
    db_req = db.query(ProcurementRequirement).filter(
        ProcurementRequirement.id == requirement_id,
        ProcurementRequirement.organization_id == current_user.organization_id
    ).first()
    if not db_req:
        raise HTTPException(status_code=404, detail="Requirement not found")

    # 2. Validate supplier exists
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    # 3. Validate attachment size & extension using Phase 4 settings
    ext = f".{file.filename.split('.')[-1].lower()}" if "." in file.filename else ""
    if ext not in settings.ALLOWED_ATTACHMENT_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Attachment extension '{ext}' is not supported. Allowed: {settings.ALLOWED_ATTACHMENT_EXTENSIONS}"
        )

    file.file.seek(0, 2)
    size_bytes = file.file.tell()
    file.file.seek(0)

    max_bytes = settings.MAX_ATTACHMENT_SIZE_MB * 1024 * 1024
    if size_bytes > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"Attachment size ({round(size_bytes / (1024*1024), 2)}MB) exceeds limit of {settings.MAX_ATTACHMENT_SIZE_MB}MB."
        )

    # 4. Extract actual text from uploaded attachment (PDF, XLSX, CSV, TXT)
    content_bytes = await file.read()
    from app.infrastructure.email.attachment_parser import extract_text_from_attachment
    text_content = extract_text_from_attachment(file.filename, content_bytes)

    full_quote_text = (
        f"SUPPLIER QUOTATION DOCUMENT ({file.filename})\n"
        f"Supplier Name: {supplier.company_name}\n\n"
        f"Document Content:\n{text_content}"
    )

    # 5. Extract structured fields using QuotationExtractionAgent
    try:
        extraction = await orchestrator.quotation_extraction_agent.execute(
            email_body=full_quote_text
        )
    except Exception as err:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to extract quotation data from '{file.filename}': {str(err)}"
        )

    # 6. Deduplicate and upsert quotation per (requirement_id, supplier_id)
    existing_quote = db.query(Quotation).filter(
        Quotation.requirement_id == requirement_id,
        Quotation.supplier_id == supplier_id
    ).first()

    if existing_quote:
        existing_quote.raw_email_body = full_quote_text
        existing_quote.extracted_data = extraction.model_dump()
        existing_quote.extraction_confidence = extraction.confidence_score
        existing_quote.received_at = datetime.utcnow()
        quote = existing_quote
    else:
        quote = Quotation(
            requirement_id=requirement_id,
            supplier_id=supplier_id,
            raw_email_body=full_quote_text,
            extracted_data=extraction.model_dump(),
            extraction_confidence=extraction.confidence_score,
            received_at=datetime.utcnow()
        )
        db.add(quote)

    db_req.status = "quoted"
    db.commit()
    db.refresh(quote)

    res = QuotationResponse.model_validate(quote)
    res.supplier_name = supplier.company_name
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


@router.get("/rfq/{rfq_id}", response_model=List[QuotationResponse])
def get_quotations_for_rfq(
    rfq_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Fetch all supplier quotations recorded for an RFQ."""
    from app.infrastructure.db.models.rfq import RFQ
    rfq_obj = db.query(RFQ).filter(RFQ.id == rfq_id).first()
    if not rfq_obj:
        raise HTTPException(status_code=404, detail="RFQ not found")

    return get_quotations_for_requirement(rfq_obj.requirement_id, current_user, db)


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
    
    rec_out = await orchestrator.recommendation_agent.execute(struct_data, quotes_payload)

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

    # 1. Update awarded quotation status to 'accepted' and all others to 'rejected'
    all_quotes = db.query(Quotation).filter(Quotation.requirement_id == requirement_id).all()
    for q in all_quotes:
        if q.supplier_id == payload.supplier_id:
            q.status = "accepted"
        else:
            q.status = "rejected"

    db_req.status = "awarded"
    db.commit()
    db.refresh(rec)

    result = RecommendationResponse.model_validate(rec)
    result.awarded_supplier_name = supplier.company_name
    return result


@router.get("/recommendation/rfq/{rfq_id}", response_model=RecommendationResponse)
async def get_or_generate_recommendation_for_rfq(
    rfq_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Fetch or generate AI recommendation for a specific RFQ."""
    from app.infrastructure.db.models.rfq import RFQ
    rfq_obj = db.query(RFQ).filter(RFQ.id == rfq_id).first()
    if not rfq_obj:
        raise HTTPException(status_code=404, detail="RFQ not found")

    return await get_or_generate_recommendation(rfq_obj.requirement_id, current_user, db)
