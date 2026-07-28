"""
Phase 2 — Team Collaboration Routes

Endpoints for adding, listing, updating, and deleting comments on
procurement requirements. Supports @mentions (stored as user ID list).

RBAC: Any authenticated team member can comment; only the comment author
      or an admin can update/delete.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.infrastructure.db.base import get_db
from app.infrastructure.db.models.comment import RequirementComment
from app.infrastructure.db.models.requirement import ProcurementRequirement
from app.infrastructure.db.models.user import User
from app.schemas.comment_schemas import CommentCreate, CommentResponse, CommentUpdate
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/requirements/{requirement_id}/comments", tags=["Comments"])


def _get_requirement_or_404(requirement_id: str, org_id: str, db: Session) -> ProcurementRequirement:
    req = (
        db.query(ProcurementRequirement)
        .filter(
            ProcurementRequirement.id == requirement_id,
            ProcurementRequirement.organization_id == org_id,
        )
        .first()
    )
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")
    return req


@router.post("/", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def add_comment(
    requirement_id: str,
    payload: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Post a comment (with optional @mentions) on a requirement."""
    _get_requirement_or_404(requirement_id, current_user.organization_id, db)

    comment = RequirementComment(
        requirement_id=requirement_id,
        author_id=current_user.id,
        body=payload.body,
        mentions=payload.mentions or [],
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


@router.get("/", response_model=List[CommentResponse])
def list_comments(
    requirement_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all comments on a requirement (chronological order)."""
    _get_requirement_or_404(requirement_id, current_user.organization_id, db)

    return (
        db.query(RequirementComment)
        .filter(RequirementComment.requirement_id == requirement_id)
        .order_by(RequirementComment.created_at.asc())
        .all()
    )


@router.patch("/{comment_id}", response_model=CommentResponse)
def update_comment(
    requirement_id: str,
    comment_id: str,
    payload: CommentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Edit a comment (author or admin only)."""
    comment = (
        db.query(RequirementComment)
        .filter(
            RequirementComment.id == comment_id,
            RequirementComment.requirement_id == requirement_id,
        )
        .first()
    )
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    # RBAC: only author or admin can edit
    if comment.author_id != current_user.id and current_user.role not in ("admin", "owner"):
        raise HTTPException(status_code=403, detail="Not authorised to edit this comment")

    comment.body = payload.body
    db.commit()
    db.refresh(comment)
    return comment


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    requirement_id: str,
    comment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a comment (author or admin only)."""
    comment = (
        db.query(RequirementComment)
        .filter(
            RequirementComment.id == comment_id,
            RequirementComment.requirement_id == requirement_id,
        )
        .first()
    )
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.author_id != current_user.id and current_user.role not in ("admin", "owner"):
        raise HTTPException(status_code=403, detail="Not authorised to delete this comment")

    db.delete(comment)
    db.commit()
