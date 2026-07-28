from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.infrastructure.db.base import get_db
from app.infrastructure.db.models.requirement import ProcurementRequirement
from app.infrastructure.db.models.user import User
from app.schemas.requirement_schemas import RequirementCreate, RequirementUpdate, RequirementResponse
from app.core.dependencies import get_current_user
from app.agents.orchestrator import orchestrator

router = APIRouter(prefix="/requirements", tags=["Requirements"])

@router.post("", response_model=RequirementResponse)
async def create_requirement(
    req: RequirementCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Run Requirement Understanding Agent
    extraction = await orchestrator.requirement_understanding_agent.execute(req.raw_text)
    
    title = req.title or f"{extraction.quantity}x {extraction.product}"

    db_req = ProcurementRequirement(
        organization_id=current_user.organization_id,
        created_by=current_user.id,
        title=title,
        raw_text=req.raw_text,
        structured_data=extraction.model_dump(),
        category=extraction.category,
        status="draft"
    )
    db.add(db_req)
    db.commit()
    db.refresh(db_req)
    return db_req

@router.get("", response_model=List[RequirementResponse])
def list_requirements(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(ProcurementRequirement)\
        .filter(ProcurementRequirement.organization_id == current_user.organization_id)\
        .order_by(ProcurementRequirement.created_at.desc())\
        .all()

@router.get("/{requirement_id}", response_model=RequirementResponse)
def get_requirement(
    requirement_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_req = db.query(ProcurementRequirement)\
        .filter(ProcurementRequirement.id == requirement_id, ProcurementRequirement.organization_id == current_user.organization_id)\
        .first()
    if not db_req:
        raise HTTPException(status_code=404, detail="Procurement requirement not found")
    return db_req

@router.patch("/{requirement_id}", response_model=RequirementResponse)
def update_requirement(
    requirement_id: str,
    update_data: RequirementUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_req = db.query(ProcurementRequirement)\
        .filter(ProcurementRequirement.id == requirement_id, ProcurementRequirement.organization_id == current_user.organization_id)\
        .first()
    if not db_req:
        raise HTTPException(status_code=404, detail="Procurement requirement not found")

    if update_data.title:
        db_req.title = update_data.title
    if update_data.structured_data:
        db_req.structured_data = update_data.structured_data
    if update_data.category:
        db_req.category = update_data.category
    if update_data.status:
        db_req.status = update_data.status

    db.commit()
    db.refresh(db_req)
    return db_req
