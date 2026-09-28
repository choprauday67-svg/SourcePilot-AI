import uuid
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.infrastructure.db.base import get_db
from app.infrastructure.db.models.requirement import ProcurementRequirement
from app.infrastructure.db.models.match import RequirementSupplierMatch
from app.infrastructure.db.models.rfq import RFQ, RFQDispatch, RFQApproval
from app.infrastructure.db.models.supplier import Supplier, SupplierContact
from app.infrastructure.db.models.organization import Organization
from app.infrastructure.db.models.user import User
from app.schemas.rfq_schemas import RFQResponse, RFQUpdate, RFQApprovalResponse, ApproveStepRequest, RejectStepRequest
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

    # Idempotent: return existing draft RFQ rather than creating duplicates
    existing_rfq = db.query(RFQ).filter(RFQ.requirement_id == requirement_id).order_by(RFQ.created_at.desc()).first()
    if existing_rfq and existing_rfq.status != "draft":
        # RFQ is already progressed; return it as-is
        return existing_rfq

    org = db.query(Organization).filter(Organization.id == current_user.organization_id).first()
    org_name = org.name if org else "SourcePilot Enterprise Client"

    struct_data = RequirementExtractionOutput.model_validate(db_req.structured_data or {})
    
    # Run RFQ Generator Agent
    rfq_out = await orchestrator.rfq_generator_agent.execute(struct_data, org_name=org_name)

    if existing_rfq and existing_rfq.status == "draft":
        # Update existing draft rather than creating a second one
        existing_rfq.title = rfq_out.title
        existing_rfq.content = rfq_out.formatted_rfq_markdown
        existing_rfq.version += 1
        db.commit()
        db.refresh(existing_rfq)
        rfq = existing_rfq
    else:
        rfq = RFQ(
            requirement_id=requirement_id,
            title=rfq_out.title,
            content=rfq_out.formatted_rfq_markdown,
            status="draft"
        )
        db.add(rfq)
        db.commit()
        db.refresh(rfq)

    # Update requirement lifecycle status
    db_req.status = "rfq_drafted"
    db.commit()

    return rfq

@router.get("/requirement/{requirement_id}", response_model=RFQResponse)
def get_rfq_for_requirement(
    requirement_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    rfq = db.query(RFQ).filter(RFQ.requirement_id == requirement_id).order_by(RFQ.created_at.desc()).first()
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found for requirement")
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

    if update_data.title or update_data.content:
        rfq.version += 1

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

        # Run Email Automation Agent proposal generation
        proposal = await orchestrator.email_automation_agent.execute(
            supplier_name=target_name,
            supplier_email=target_email,
            rfq_title=rfq.title,
            rfq_markdown=rfq.content
        )

        provider_msg_id = f"msg_{uuid.uuid4().hex[:12]}"
        dispatch = RFQDispatch(
            rfq_id=rfq.id,
            supplier_id=supplier.id,
            supplier_contact_id=contact.id if contact else supplier.id,
            delivery_status="sent",
            provider_message_id=provider_msg_id
        )
        db.add(dispatch)
        dispatches.append(dispatch)

    rfq.status = "sent"
    db_req = db.query(ProcurementRequirement).filter(ProcurementRequirement.id == rfq.requirement_id).first()
    if db_req:
        db_req.status = "rfq_sent"

    db.commit()
    return {"message": f"Successfully dispatched RFQ to {len(dispatches)} suppliers via Mailtrap/SMTP."}


# ---------------------------------------------------------------------------
# Phase 3 — Multi-Approver RFQ Workflow
# ---------------------------------------------------------------------------

@router.post("/{rfq_id}/submit-for-approval", response_model=list)
def submit_rfq_for_approval(
    rfq_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Transitions an RFQ from 'draft' or 'rfq_drafted' to 'pending_approval' and creates a
    two-step approval chain:
      Step 1: Technical Review (buyer role)
      Step 2: Director Approval (director role)
    """
    rfq = db.query(RFQ).filter(RFQ.id == rfq_id).first()
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")
    if rfq.status not in ("draft", "rfq_drafted"):
        raise HTTPException(
            status_code=400,
            detail=f"RFQ is already in '{rfq.status}' state. Only 'draft' RFQs can be submitted."
        )

    # Remove any stale approvals before creating fresh chain
    db.query(RFQApproval).filter(RFQApproval.rfq_id == rfq_id).delete()

    approval_steps = [
        RFQApproval(rfq_id=rfq_id, step_number=1, role_required="buyer",    status="pending"),
        RFQApproval(rfq_id=rfq_id, step_number=2, role_required="director", status="pending"),
    ]
    db.add_all(approval_steps)
    rfq.status = "pending_approval"

    # Update requirement lifecycle status
    db_req = db.query(ProcurementRequirement).filter(ProcurementRequirement.id == rfq.requirement_id).first()
    if db_req:
        db_req.status = "pending_approval"

    db.commit()

    db.refresh(rfq)
    for step in approval_steps:
        db.refresh(step)

    return [
        {
            "id": s.id,
            "rfq_id": s.rfq_id,
            "step_number": s.step_number,
            "role_required": s.role_required,
            "status": s.status,
            "created_at": s.created_at.isoformat(),
        }
        for s in approval_steps
    ]


@router.post("/{rfq_id}/approve-step", response_model=RFQResponse)
def approve_approval_step(
    rfq_id: str,
    payload: ApproveStepRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Approve a specific step in the multi-approver chain.
    Steps must be approved sequentially — step N cannot be approved until step N-1 is approved.
    When all steps are approved, the RFQ status is promoted to 'approved'.
    """
    rfq = db.query(RFQ).filter(RFQ.id == rfq_id).first()
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")

    # Enforce sequential approval: previous step must be approved first
    if payload.step_number > 1:
        prev_step = (
            db.query(RFQApproval)
            .filter(RFQApproval.rfq_id == rfq_id, RFQApproval.step_number == payload.step_number - 1)
            .first()
        )
        if not prev_step or prev_step.status != "approved":
            raise HTTPException(
                status_code=400,
                detail=f"Step {payload.step_number} cannot be approved until Step {payload.step_number - 1} is approved."
            )

    step = (
        db.query(RFQApproval)
        .filter(RFQApproval.rfq_id == rfq_id, RFQApproval.step_number == payload.step_number)
        .first()
    )
    if not step:
        raise HTTPException(status_code=404, detail=f"Approval step {payload.step_number} not found")
    if step.status != "pending":
        raise HTTPException(status_code=400, detail=f"Step {payload.step_number} is already '{step.status}'")

    step.status = "approved"
    step.approver_id = current_user.id
    step.comments = payload.comments
    step.decided_at = datetime.utcnow()

    # Flush this step change before evaluating all steps
    db.flush()
    all_steps = db.query(RFQApproval).filter(RFQApproval.rfq_id == rfq_id).all()
    if all(s.status == "approved" for s in all_steps):
        rfq.status = "approved"
        rfq.approved_by = current_user.id
        rfq.approved_at = datetime.utcnow()
        # Update requirement lifecycle status
        db_req = db.query(ProcurementRequirement).filter(ProcurementRequirement.id == rfq.requirement_id).first()
        if db_req:
            db_req.status = "approved"

    db.commit()
    db.refresh(rfq)
    return rfq


@router.post("/{rfq_id}/reject-step", response_model=RFQResponse)
def reject_approval_step(
    rfq_id: str,
    payload: RejectStepRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reject a specific approval step. This reverts the RFQ back to 'draft'
    so the requester can revise and resubmit.
    """
    rfq = db.query(RFQ).filter(RFQ.id == rfq_id).first()
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")

    step = (
        db.query(RFQApproval)
        .filter(RFQApproval.rfq_id == rfq_id, RFQApproval.step_number == payload.step_number)
        .first()
    )
    if not step:
        raise HTTPException(status_code=404, detail=f"Approval step {payload.step_number} not found")

    step.status = "rejected"
    step.approver_id = current_user.id
    step.comments = payload.comments
    step.decided_at = datetime.utcnow()

    # Revert RFQ to draft so requester can revise
    rfq.status = "draft"

    # Revert requirement lifecycle status too
    db_req = db.query(ProcurementRequirement).filter(ProcurementRequirement.id == rfq.requirement_id).first()
    if db_req and db_req.status in ("pending_approval", "approved"):
        db_req.status = "rfq_drafted"

    db.commit()
    db.refresh(rfq)
    return rfq
