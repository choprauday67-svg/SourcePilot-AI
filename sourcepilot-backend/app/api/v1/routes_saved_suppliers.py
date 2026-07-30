"""
Phase 3 — Saved Supplier Library Routes

Endpoints for bookmarking/saving suppliers, managing organization directory,
updating notes/tags, and attaching saved suppliers directly to requirements.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.infrastructure.db.base import get_db
from app.infrastructure.db.models.saved_supplier import SavedSupplier
from app.infrastructure.db.models.supplier import Supplier
from app.infrastructure.db.models.match import RequirementSupplierMatch
from app.infrastructure.db.models.user import User
from app.schemas.saved_supplier_schemas import (
    SavedSupplierCreate,
    SavedSupplierUpdate,
    SavedSupplierResponse,
    SelectSavedSuppliersRequest,
)
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/saved-suppliers", tags=["Saved Suppliers"])


@router.post("/", response_model=SavedSupplierResponse, status_code=status.HTTP_201_CREATED)
def save_supplier(
    payload: SavedSupplierCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Save/bookmark a supplier into organization directory."""
    supplier = db.query(Supplier).filter(Supplier.id == payload.supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    existing = (
        db.query(SavedSupplier)
        .options(joinedload(SavedSupplier.supplier))
        .filter(
            SavedSupplier.organization_id == current_user.organization_id,
            SavedSupplier.supplier_id == payload.supplier_id,
        )
        .first()
    )
    if existing:
        # Update existing saved entry
        if payload.category: existing.category = payload.category
        if payload.status: existing.status = payload.status
        if payload.tags: existing.tags = payload.tags
        if payload.notes: existing.notes = payload.notes
        db.commit()
        db.refresh(existing)
        return existing

    saved = SavedSupplier(
        organization_id=current_user.organization_id,
        supplier_id=payload.supplier_id,
        saved_by_user_id=current_user.id,
        category=payload.category or "General",
        status=payload.status or "preferred",
        tags=payload.tags or [],
        notes=payload.notes or "",
    )
    db.add(saved)
    db.commit()
    return (
        db.query(SavedSupplier)
        .options(joinedload(SavedSupplier.supplier))
        .filter(SavedSupplier.id == saved.id)
        .first()
    )


@router.get("/", response_model=List[SavedSupplierResponse])
def list_saved_suppliers(
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List organization's saved supplier library."""
    query = (
        db.query(SavedSupplier)
        .options(joinedload(SavedSupplier.supplier))
        .filter(SavedSupplier.organization_id == current_user.organization_id)
    )
    if category:
        query = query.filter(SavedSupplier.category == category)
    return query.order_by(SavedSupplier.created_at.desc()).all()


@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_saved_supplier(
    supplier_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a supplier from saved library."""
    saved = (
        db.query(SavedSupplier)
        .filter(
            SavedSupplier.organization_id == current_user.organization_id,
            SavedSupplier.supplier_id == supplier_id,
        )
        .first()
    )
    if not saved:
        raise HTTPException(status_code=404, detail="Saved supplier entry not found")

    db.delete(saved)
    db.commit()


@router.post("/attach-to-requirement/{requirement_id}")
def attach_saved_suppliers_to_requirement(
    requirement_id: str,
    payload: SelectSavedSuppliersRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Attach selected saved suppliers directly to a requirement's match list without re-querying connectors."""
    attached = 0
    for supplier_id in payload.supplier_ids:
        existing_match = (
            db.query(RequirementSupplierMatch)
            .filter(
                RequirementSupplierMatch.requirement_id == requirement_id,
                RequirementSupplierMatch.supplier_id == supplier_id,
            )
            .first()
        )
        if not existing_match:
            match = RequirementSupplierMatch(
                requirement_id=requirement_id,
                supplier_id=supplier_id,
                rank_score=92.0,  # Preferred library supplier default baseline
                rank_explanation={
                    "summary": "Selected directly from Organization Saved Supplier Library.",
                    "price_fit": "Historical Preferred Tier",
                    "certification_match": "Verified Library Vendor",
                    "lead_time": "Pre-screened supplier",
                    "trust_score": 92.0,
                    "source_connector": "saved_library",
                },
                selected_by_user=True,
            )
            db.add(match)
            attached += 1

    db.commit()
    return {"message": f"Successfully attached {attached} saved suppliers to requirement."}
