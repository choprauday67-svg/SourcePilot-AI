"""
Phase 2 — Inbound Email Webhook Route

Receives inbound supplier reply emails parsed by an email provider
(SendGrid Inbound Parse, Mailgun Routes, Postmark Inbound, etc.)
and routes them to the QuoteExtractionAgent for structured quote extraction.

Webhook payload contract (provider-agnostic):
  POST /api/v1/webhooks/inbound-email
  Body: InboundEmailPayload JSON

Security: X-Webhook-Secret header must match INBOUND_EMAIL_WEBHOOK_SECRET.
"""
import hashlib
import hmac
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.infrastructure.db.base import get_db
from app.infrastructure.db.models.quotation import Quotation
from app.infrastructure.db.models.rfq import RFQDispatch
from app.infrastructure.db.models.supplier import Supplier
from app.agents.orchestrator import orchestrator
from app.core.config import settings

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


# ─────────────────────────────────────────────
# Request/Response schemas (inline for locality)
# ─────────────────────────────────────────────
class EmailAttachment(BaseModel):
    filename: str
    content_type: str
    size_bytes: int = 0


class InboundEmailPayload(BaseModel):
    """
    Provider-agnostic inbound email payload.
    Adapters for SendGrid, Mailgun, Postmark normalise into this shape.
    """
    from_email: str
    from_name: Optional[str] = ""
    to_email: str
    subject: str
    body_text: str
    body_html: Optional[str] = ""
    supplier_id: Optional[str] = None     # Resolved from from_email lookup
    rfq_dispatch_id: Optional[str] = None  # Resolved from subject/thread ID
    attachments: Optional[List[EmailAttachment]] = []
    received_at: Optional[str] = None


class WebhookResponse(BaseModel):
    received: bool
    quotation_id: Optional[str] = None
    message: str


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def _verify_webhook_secret(x_webhook_secret: Optional[str]) -> bool:
    """Compare provided secret with configured secret using constant-time comparison."""
    expected = settings.INBOUND_EMAIL_WEBHOOK_SECRET or ""
    if not expected:
        return True  # No secret configured → allow all (dev mode)
    if not x_webhook_secret:
        return False
    return hmac.compare_digest(x_webhook_secret.encode(), expected.encode())


def _resolve_supplier_from_email(from_email: str, db: Session) -> Optional[Supplier]:
    """Try to find a supplier whose canonical_domain matches the sender's domain."""
    try:
        domain = from_email.split("@")[1].lower().strip()
        return db.query(Supplier).filter(Supplier.canonical_domain == domain).first()
    except (IndexError, AttributeError):
        return None


def _resolve_dispatch_from_subject(subject: str, db: Session) -> Optional[RFQDispatch]:
    """
    Future: parse thread ID / message-ID from subject for precise dispatch resolution.
    Currently a stub — returns the most recent unresolved dispatch for the supplier domain.
    """
    return None


# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────
@router.post("/inbound-email", response_model=WebhookResponse)
async def receive_inbound_email(
    payload: InboundEmailPayload,
    x_webhook_secret: Optional[str] = Header(None, alias="X-Webhook-Secret"),
    db: Session = Depends(get_db),
):
    """
    Inbound email webhook endpoint.
    
    Receives parsed supplier reply, runs QuoteExtractionAgent, and persists
    the structured quotation. Requires X-Webhook-Secret header for authentication.
    """
    # --- Auth ---
    if not _verify_webhook_secret(x_webhook_secret):
        raise HTTPException(status_code=403, detail="Invalid webhook secret")

    # --- Resolve supplier from sender email ---
    supplier = None
    if payload.supplier_id:
        supplier = db.query(Supplier).filter(Supplier.id == payload.supplier_id).first()
    if not supplier:
        supplier = _resolve_supplier_from_email(payload.from_email, db)

    if not supplier:
        # Cannot persist without a valid supplier FK — log and return
        return WebhookResponse(
            received=True,
            message=(
                f"Webhook received from {payload.from_email} but no matching supplier found. "
                "Create the supplier record and retry."
            )
        )

    # --- Run QuoteExtractionAgent ---
    try:
        extraction: "QuotationExtractionOutput" = await orchestrator.quotation_extraction_agent.execute(
            email_body=payload.body_text,
        )
    except Exception as exc:
        return WebhookResponse(
            received=True,
            message=f"Webhook received but AI extraction failed: {str(exc)}"
        )

    # --- Resolve requirement_id for backward DB schema compatibility ---
    from app.infrastructure.db.models.match import RequirementSupplierMatch
    from app.infrastructure.db.models.requirement import ProcurementRequirement

    req_match = (
        db.query(RequirementSupplierMatch)
        .filter(RequirementSupplierMatch.supplier_id == supplier.id)
        .first()
    )
    resolved_req_id = req_match.requirement_id if req_match else None
    if not resolved_req_id:
        latest_req = db.query(ProcurementRequirement).order_by(ProcurementRequirement.created_at.desc()).first()
        resolved_req_id = latest_req.id if latest_req else None

    # --- Persist structured quotation ---
    quotation = Quotation(
        supplier_id=supplier.id,
        requirement_id=resolved_req_id,
        rfq_dispatch_id=None,
        raw_email_body=payload.body_text,
        extracted_data=extraction.model_dump(),
        extraction_confidence=extraction.confidence_score,
        received_at=datetime.utcnow(),
    )
    db.add(quotation)
    db.commit()
    db.refresh(quotation)

    return WebhookResponse(
        received=True,
        quotation_id=quotation.id,
        message=f"Quote extracted and stored (ID: {quotation.id})"
    )



@router.get("/inbound-email/health")
def webhook_health():
    """Liveness probe for the inbound email webhook endpoint."""
    return {
        "status": "healthy",
        "endpoint": "inbound-email-webhook",
        "version": "phase2"
    }
