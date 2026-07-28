from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.infrastructure.db.base import get_db
from app.infrastructure.db.models.requirement import ProcurementRequirement
from app.infrastructure.db.models.match import RequirementSupplierMatch
from app.infrastructure.db.models.rfq import RFQ, RFQDispatch
from app.infrastructure.db.models.supplier import Supplier, SupplierContact
from app.infrastructure.db.models.organization import Organization
from app.infrastructure.db.models.user import User
from app.schemas.rfq_schemas import RFQResponse, RFQUpdate
from app.schemas.agent_io_schemas import RequirementExtractionOutput
from app.core.dependencies import get_current_user
from app.agents.orchestrator import orchestrator

router = APIRouter(prefix="/rfq", tags=["RFQ"])

@router.post("/generate/{requirement_id}", response_model=RFQResponse)
async def generate_rfq_draft(
    requirement_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_req = db.query(ProcurementRequirement)\
        .filter(ProcurementRequirement.id == requirement_id, ProcurementRequirement.organization_id == current_user.organization_id)\
        .first()
    if not db_req:
        raise HTTPException(status_code=404, detail="Requirement not found")

    org = db.query(Organization).filter(Organization.id == current_user.organization_id).first()
    org_name = org.name if org else "SourcePilot Enterprise Client"

    struct_data = RequirementExtractionOutput.model_validate(db_req.structured_data or {})
    
    # Run RFQ Generator Agent
    rfq_out = await orchestrator.rfq_generator_agent.execute(struct_data, org_name=org_name)

    rfq = RFQ(
        requirement_id=requirement_id,
        title=rfq_out.title,
        content=rfq_out.formatted_rfq_markdown,
        status="draft"
    )
    db.add(rfq)
    db.commit()
    db.refresh(rfq)
    return rfq

@router.get("/{rfq_id}", response_model=RFQResponse)
def get_rfq(
    rfq_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    rfq = db.query(RFQ).filter(RFQ.id == rfq_id).first()
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")
    return rfq

@router.patch("/{rfq_id}", response_model=RFQResponse)
def update_rfq(
    rfq_id: str,
    update_data: RFQUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    rfq = db.query(RFQ).filter(RFQ.id == rfq_id).first()
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")

    if update_data.title:
        rfq.title = update_data.title
    if update_data.content:
        rfq.content = update_data.content
        rfq.version += 1

    db.commit()
    db.refresh(rfq)
    return rfq

@router.post("/{rfq_id}/approve", response_model=RFQResponse)
def approve_rfq(
    rfq_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    rfq = db.query(RFQ).filter(RFQ.id == rfq_id).first()
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")

    rfq.status = "approved"
    rfq.approved_by = current_user.id
    rfq.approved_at = datetime.utcnow()

    db.commit()
    db.refresh(rfq)
    return rfq

@router.post("/{rfq_id}/send")
async def send_rfq_to_selected_suppliers(
    rfq_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    rfq = db.query(RFQ).filter(RFQ.id == rfq_id).first()
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")
    if rfq.status != "approved":
        raise HTTPException(status_code=400, detail="RFQ must be approved before dispatching.")

    # Find selected suppliers
    selected_matches = db.query(RequirementSupplierMatch)\
        .filter(RequirementSupplierMatch.requirement_id == rfq.requirement_id, RequirementSupplierMatch.selected_by_user == True)\
        .all()

    if not selected_matches:
        # Fallback to top matches if none explicitly toggled
        selected_matches = db.query(RequirementSupplierMatch)\
            .filter(RequirementSupplierMatch.requirement_id == rfq.requirement_id)\
            .order_by(RequirementSupplierMatch.rank_score.desc())\
            .limit(3)\
            .all()

    dispatches = []
    for match in selected_matches:
        supplier = db.query(Supplier).filter(Supplier.id == match.supplier_id).first()
        contact = db.query(SupplierContact).filter(SupplierContact.supplier_id == supplier.id).first()
        
        target_email = contact.email if contact else f"sales@{supplier.canonical_domain}"
        target_name = supplier.company_name

        # Run Email Automation Agent
        send_result = await orchestrator.email_automation_agent.execute(
            supplier_name=target_name,
            supplier_email=target_email,
            rfq_title=rfq.title,
            rfq_markdown=rfq.content
        )

        dispatch = RFQDispatch(
            rfq_id=rfq.id,
            supplier_id=supplier.id,
            supplier_contact_id=contact.id if contact else supplier.id,
            delivery_status="sent" if send_result.success else "bounced",
            provider_message_id=send_result.provider_message_id
        )
        db.add(dispatch)
        dispatches.append(dispatch)

    rfq.status = "sent"
    db_req = db.query(ProcurementRequirement).filter(ProcurementRequirement.id == rfq.requirement_id).first()
    if db_req:
        db_req.status = "rfq_sent"

    db.commit()
    return {"message": f"Successfully dispatched RFQ to {len(dispatches)} suppliers via Mailtrap/SMTP."}
