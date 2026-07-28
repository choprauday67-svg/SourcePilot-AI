from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.infrastructure.db.base import get_db
from app.infrastructure.db.models.requirement import ProcurementRequirement
from app.infrastructure.db.models.supplier import Supplier, SupplierContact, SupplierProfile
from app.infrastructure.db.models.match import RequirementSupplierMatch
from app.infrastructure.db.models.user import User
from app.schemas.supplier_schemas import SupplierRankedMatchResponse, SupplierSelectionRequest
from app.schemas.agent_io_schemas import RequirementExtractionOutput
from app.core.dependencies import get_current_user
from app.agents.orchestrator import orchestrator

router = APIRouter(prefix="/requirements/{requirement_id}/suppliers", tags=["Suppliers"])

@router.post("/discover", response_model=List[SupplierRankedMatchResponse])
async def discover_and_rank_suppliers(
    requirement_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_req = db.query(ProcurementRequirement)\
        .filter(ProcurementRequirement.id == requirement_id, ProcurementRequirement.organization_id == current_user.organization_id)\
        .first()
    if not db_req:
        raise HTTPException(status_code=404, detail="Requirement not found")

    db_req.status = "discovering"
    db.commit()

    struct_data = RequirementExtractionOutput.model_validate(db_req.structured_data or {})
    
    # 1. Run Supplier Discovery Agent
    candidates = await orchestrator.supplier_discovery_agent.execute(struct_data, limit=5)
    
    # 2. Persist/Enrich Suppliers & Profiles
    supplier_records = []
    for cand in candidates:
        supplier = db.query(Supplier).filter(Supplier.canonical_domain == cand.canonical_domain).first()
        if not supplier:
            supplier = Supplier(
                company_name=cand.company_name,
                website=cand.website,
                canonical_domain=cand.canonical_domain,
                location_country=cand.country,
                location_city=cand.city
            )
            db.add(supplier)
            db.flush()

            # Create default contact
            contact = SupplierContact(
                supplier_id=supplier.id,
                email=cand.contact_email or f"sales@{cand.canonical_domain}",
                phone=cand.contact_phone,
                contact_name=f"Sales Team - {cand.company_name}",
                is_primary=True,
                source_connector=cand.source_connector
            )
            db.add(contact)

        # Intelligence Enrichment Agent
        intel = await orchestrator.supplier_intelligence_agent.execute(cand)
        
        profile = SupplierProfile(
            supplier_id=supplier.id,
            requirement_id=requirement_id,
            rating=cand.rating,
            certifications=cand.certifications,
            moq=cand.raw_metadata.get("moq", "100 units"),
            lead_time_days=cand.raw_metadata.get("lead_time_days", 14),
            trust_score=intel["trust_score"],
            risk_flags=intel["risk_flags"]
        )
        db.add(profile)
        db.flush()

        supplier_records.append({
            "id": supplier.id,
            "company_name": supplier.company_name,
            "profile": intel
        })

    # 3. Run Ranking Agent
    ranking_output = await orchestrator.supplier_ranking_agent.execute(struct_data, supplier_records)

    # 4. Save matches in DB
    matches = []
    # Clear existing matches if re-ranking
    db.query(RequirementSupplierMatch).filter(RequirementSupplierMatch.requirement_id == requirement_id).delete()

    for rank_item in ranking_output.rankings:
        match = RequirementSupplierMatch(
            requirement_id=requirement_id,
            supplier_id=rank_item.supplier_id,
            rank_score=rank_item.rank_score,
            rank_explanation=rank_item.rank_explanation
        )
        db.add(match)
        db.flush()
        matches.append(match)

    db_req.status = "ranked"
    db.commit()

    return get_ranked_suppliers(requirement_id, current_user, db)

@router.get("", response_model=List[SupplierRankedMatchResponse])
def get_ranked_suppliers(
    requirement_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    matches = db.query(RequirementSupplierMatch)\
        .join(ProcurementRequirement)\
        .filter(RequirementSupplierMatch.requirement_id == requirement_id, ProcurementRequirement.organization_id == current_user.organization_id)\
        .order_by(RequirementSupplierMatch.rank_score.desc())\
        .all()

    result = []
    for m in matches:
        sup = db.query(Supplier).filter(Supplier.id == m.supplier_id).first()
        result.append({
            "match_id": m.id,
            "supplier": sup,
            "rank_score": m.rank_score,
            "rank_explanation": m.rank_explanation,
            "selected_by_user": m.selected_by_user
        })
    return result

@router.post("/select")
def select_suppliers_for_rfq(
    requirement_id: str,
    req: SupplierSelectionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Clear existing selection
    db.query(RequirementSupplierMatch)\
        .filter(RequirementSupplierMatch.requirement_id == requirement_id)\
        .update({"selected_by_user": False})

    # Mark requested suppliers selected
    db.query(RequirementSupplierMatch)\
        .filter(RequirementSupplierMatch.requirement_id == requirement_id, RequirementSupplierMatch.supplier_id.in_(req.supplier_ids))\
        .update({"selected_by_user": True, "selected_at": datetime.utcnow()}, synchronize_session=False)

    db.commit()
    return {"message": f"Successfully selected {len(req.supplier_ids)} suppliers for RFQ."}
