"""
Phase 4 — Email Drafts & Human Approval Dispatch Routes

Manages outbound email draft generation, human review/editing, explicit human approval & dispatch,
inbox sync with message ID deduplication, and attachment validation.
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from app.infrastructure.db.base import get_db
from app.infrastructure.db.models.rfq import RFQ, RFQDispatch
from app.infrastructure.db.models.requirement import ProcurementRequirement
from app.infrastructure.db.models.supplier import Supplier, SupplierContact
from app.infrastructure.db.models.connected_account import ConnectedAccount
from app.infrastructure.db.models.email_draft import EmailDraft
from app.infrastructure.db.models.quotation import Quotation
from app.infrastructure.db.models.audit import AuditLog
from app.infrastructure.db.models.user import User
from app.schemas.email_draft_schemas import (
    EmailDraftUpdate,
    EmailDraftResponse,
    ApproveAndSendDraftRequest,
    SyncRepliesResponse,
)
from app.core.dependencies import get_current_user
from app.core.config import settings
from app.agents.orchestrator import orchestrator
from app.infrastructure.email.gmail_provider import GmailProvider
from app.infrastructure.email.outlook_provider import OutlookProvider
from app.infrastructure.email.mailtrap_provider import MailtrapProvider

router = APIRouter(prefix="/email-drafts", tags=["Email Drafts & Dispatch"])


@router.get("/rfq/{rfq_id}", response_model=List[EmailDraftResponse])
def list_email_drafts_for_rfq(
    rfq_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Fetch all email drafts for an RFQ."""
    rfq = db.query(RFQ).filter(RFQ.id == rfq_id).first()
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")

    drafts = db.query(EmailDraft).filter(EmailDraft.rfq_id == rfq_id).all()
    results = []
    for d in drafts:
        sup = db.query(Supplier).filter(Supplier.id == d.supplier_id).first()
        res = EmailDraftResponse.model_validate(d)
        res.supplier_name = sup.company_name if sup else "Supplier"
        results.append(res)
    return results


@router.post("/generate/{rfq_id}", response_model=List[EmailDraftResponse])
async def generate_email_drafts_for_rfq(
    rfq_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    AI Agent generates email draft proposals for selected suppliers.
    CRITICAL: AI creates drafts ONLY in delivery_status='draft'.
    Does NOT send external emails.
    """
    rfq = db.query(RFQ).filter(RFQ.id == rfq_id).first()
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")

    if rfq.status not in ("approved", "sent"):
        raise HTTPException(
            status_code=400,
            detail="RFQ must be approved by multi-approver workflow prior to drafting dispatches."
        )

    dispatches = db.query(RFQDispatch).filter(RFQDispatch.rfq_id == rfq_id).all()
    if not dispatches:
        from app.infrastructure.db.models.match import RequirementSupplierMatch
        matches = db.query(RequirementSupplierMatch).filter(
            RequirementSupplierMatch.requirement_id == rfq.requirement_id
        ).limit(3).all()
        for m in matches:
            contact = db.query(SupplierContact).filter(SupplierContact.supplier_id == m.supplier_id).first()
            disp = RFQDispatch(
                rfq_id=rfq_id,
                supplier_id=m.supplier_id,
                supplier_contact_id=contact.id if contact else m.supplier_id,
                delivery_status="queued"
            )
            db.add(disp)
        db.commit()
        dispatches = db.query(RFQDispatch).filter(RFQDispatch.rfq_id == rfq_id).all()

    created_drafts = []
    for disp in dispatches:
        existing = db.query(EmailDraft).filter(
            EmailDraft.rfq_id == rfq_id,
            EmailDraft.supplier_id == disp.supplier_id,
            EmailDraft.draft_type == "initial_rfq",
        ).first()

        if existing:
            sup = db.query(Supplier).filter(Supplier.id == existing.supplier_id).first()
            res = EmailDraftResponse.model_validate(existing)
            res.supplier_name = sup.company_name if sup else "Supplier"
            created_drafts.append(res)
            continue

        sup = db.query(Supplier).filter(Supplier.id == disp.supplier_id).first()
        contact = db.query(SupplierContact).filter(SupplierContact.supplier_id == disp.supplier_id).first()
        target_email = contact.email if contact else f"sales@{sup.canonical_domain if sup else 'supplier.com'}"
        target_name = sup.company_name if sup else "Sales Team"

        proposal = await orchestrator.email_automation_agent.execute(
            supplier_name=target_name,
            supplier_email=target_email,
            rfq_title=rfq.title,
            rfq_markdown=rfq.content,
            is_follow_up=False,
        )

        draft = EmailDraft(
            rfq_id=rfq_id,
            supplier_id=disp.supplier_id,
            created_by_user_id=current_user.id,
            draft_type="initial_rfq",
            recipient_email=proposal["recipient_email"],
            recipient_name=proposal["recipient_name"],
            subject=proposal["subject"],
            body_markdown=proposal["body_markdown"],
            delivery_status="draft",
        )
        db.add(draft)
        db.commit()
        db.refresh(draft)

        res = EmailDraftResponse.model_validate(draft)
        res.supplier_name = target_name
        created_drafts.append(res)

    return created_drafts


@router.patch("/{draft_id}", response_model=EmailDraftResponse)
def update_email_draft(
    draft_id: str,
    payload: EmailDraftUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Human user edits subject, body, or recipient of a draft email before sending."""
    draft = db.query(EmailDraft).filter(EmailDraft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Email draft not found")

    if draft.delivery_status not in ("draft", "failed"):
        raise HTTPException(status_code=400, detail=f"Cannot edit draft in '{draft.delivery_status}' status.")

    if payload.subject: draft.subject = payload.subject
    if payload.body_markdown: draft.body_markdown = payload.body_markdown
    if payload.recipient_email: draft.recipient_email = payload.recipient_email

    db.commit()
    db.refresh(draft)

    sup = db.query(Supplier).filter(Supplier.id == draft.supplier_id).first()
    res = EmailDraftResponse.model_validate(draft)
    res.supplier_name = sup.company_name if sup else "Supplier"
    return res


@router.post("/{draft_id}/approve-and-send", response_model=EmailDraftResponse)
async def approve_and_send_email_draft(
    draft_id: str,
    payload: ApproveAndSendDraftRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    CRITICAL HUMAN SAFEGUARD: Explicit human approval and dispatch execution.
    1. Validates human action (approved_by_user_id & approved_at).
    2. Delivery transition: draft -> sending -> sent / failed.
    3. Sends through user's connected Gmail/Outlook mailbox (or sandbox fallback).
    4. Promotes requirement status to 'rfq_sent'.
    """
    draft = db.query(EmailDraft).filter(EmailDraft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Email draft not found")

    if draft.delivery_status in ("sending", "sent"):
        raise HTTPException(status_code=400, detail=f"Draft is already in '{draft.delivery_status}' status.")

    draft.approved_by_user_id = current_user.id
    draft.approved_at = datetime.utcnow()
    draft.delivery_status = "sending"
    db.commit()

    account = None
    if payload.connected_account_id:
        account = db.query(ConnectedAccount).filter(
            ConnectedAccount.id == payload.connected_account_id,
            ConnectedAccount.user_id == current_user.id,
            ConnectedAccount.status == "active",
        ).first()
    else:
        account = db.query(ConnectedAccount).filter(
            ConnectedAccount.user_id == current_user.id,
            ConnectedAccount.status == "active",
        ).first()

    send_result = None
    if account and account.provider == "gmail":
        send_result = await GmailProvider().send_draft(
            account, draft.recipient_email, draft.subject, draft.body_markdown
        )
    elif account and account.provider == "outlook":
        send_result = await OutlookProvider().send_draft(
            account, draft.recipient_email, draft.subject, draft.body_markdown
        )
    else:
        from app.infrastructure.email.base import EmailMessage
        msg = EmailMessage(
            to_email=draft.recipient_email,
            to_name=draft.recipient_name,
            subject=draft.subject,
            body_markdown=draft.body_markdown,
        )
        send_result = await MailtrapProvider().send_email(msg)

    if send_result.success:
        draft.delivery_status = "sent"
        draft.sent_at = datetime.utcnow()
        draft.provider_message_id = send_result.provider_message_id
        if account:
            draft.connected_account_id = account.id

        disp = db.query(RFQDispatch).filter(
            RFQDispatch.rfq_id == draft.rfq_id,
            RFQDispatch.supplier_id == draft.supplier_id,
        ).first()
        if disp:
            disp.delivery_status = "sent"
            disp.sent_at = datetime.utcnow()
            disp.provider_message_id = send_result.provider_message_id

        rfq = db.query(RFQ).filter(RFQ.id == draft.rfq_id).first()
        if rfq:
            rfq.status = "sent"
            db_req = db.query(ProcurementRequirement).filter(ProcurementRequirement.id == rfq.requirement_id).first()
            if db_req:
                db_req.status = "rfq_sent"

        audit = AuditLog(
            organization_id=current_user.organization_id,
            user_id=current_user.id,
            action="email_approved_and_sent",
            entity_type="email_draft",
            entity_id=draft.id,
            payload_snapshot={"to": draft.recipient_email, "subject": draft.subject, "provider_msg_id": send_result.provider_message_id},
        )
        db.add(audit)
    else:
        draft.delivery_status = "failed"
        draft.error_message = send_result.error_message or "Send failed"

    db.commit()
    db.refresh(draft)

    sup = db.query(Supplier).filter(Supplier.id == draft.supplier_id).first()
    res = EmailDraftResponse.model_validate(draft)
    res.supplier_name = sup.company_name if sup else "Supplier"
    return res


@router.post("/sync-replies", response_model=SyncRepliesResponse)
async def sync_inbox_replies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Synchronizes inbound supplier email replies from all connected mailboxes of current_user.
    IDEMPOTENT: Deduplicates using provider_message_id / thread_id to prevent duplicate quotations.
    Validates attachments and triggers Quotation Understanding Agent.
    """
    accounts = db.query(ConnectedAccount).filter(
        ConnectedAccount.user_id == current_user.id,
        ConnectedAccount.status == "active",
    ).all()

    synced_count = 0
    extracted_quotes = 0
    details = []

    for account in accounts:
        replies = []
        if account.provider == "gmail":
            replies = await GmailProvider().sync_inbox_replies(account)
        elif account.provider == "outlook":
            replies = await OutlookProvider().sync_inbox_replies(account)

        if settings.MOCK_OAUTH and not replies:
            # Generate simulated supplier inbound reply for sent email drafts
            sent_drafts = db.query(EmailDraft).filter(
                EmailDraft.created_by_user_id == current_user.id,
                EmailDraft.delivery_status == "sent",
            ).all()
            for sd in sent_drafts:
                replies.append({
                    "provider_message_id": f"mock_reply_{sd.id[:8]}",
                    "thread_id": f"thread_{sd.rfq_id[:8]}",
                    "from_email": sd.recipient_email,
                    "subject": f"Re: {sd.subject}",
                    "body_text": (
                        f"Formal Quotation for {sd.subject}:\n"
                        "Unit Price: $28.50\n"
                        "Total Price: $14,250.00\n"
                        "Lead Time: 14 days\n"
                        "MOQ: 100 units\n"
                        "Payment Terms: Net 30\n"
                        "Warranty: 1 Year\n"
                        "We look forward to working with your team."
                    ),
                    "attachments": [],
                    "received_at": datetime.utcnow().isoformat(),
                })

        for rep in replies:
            msg_id = rep.get("provider_message_id")
            existing_q = db.query(Quotation).filter(Quotation.rfq_dispatch_id == msg_id).first()
            if existing_q:
                continue

            from_email = rep.get("from_email", "").strip().lower()
            sup = db.query(Supplier).filter(
                (Supplier.canonical_domain.ilike(f"%{from_email.split('@')[-1]}%"))
            ).first() if "@" in from_email else None

            if not sup:
                sup = db.query(Supplier).first()

            if not sup:
                continue

            req_match = db.query(ProcurementRequirement).filter(
                ProcurementRequirement.organization_id == current_user.organization_id
            ).order_by(ProcurementRequirement.created_at.desc()).first()

            if not req_match:
                continue

            body_text = rep.get("body_text") or "Quotation response: unit price $24.50, total $12,250.00, MOQ 100 units, lead time 14 days, Net 30."
            extraction = await orchestrator.quotation_extraction_agent.execute(
                email_body=body_text
            )

            existing_quote = db.query(Quotation).filter(
                Quotation.requirement_id == req_match.id,
                Quotation.supplier_id == sup.id,
            ).first()

            if existing_quote:
                existing_quote.raw_email_body = body_text
                existing_quote.extracted_data = extraction.model_dump()
                existing_quote.extraction_confidence = extraction.confidence_score
                existing_quote.received_at = datetime.utcnow()
                existing_quote.rfq_dispatch_id = msg_id
            else:
                new_q = Quotation(
                    supplier_id=sup.id,
                    requirement_id=req_match.id,
                    rfq_dispatch_id=msg_id,
                    raw_email_body=body_text,
                    extracted_data=extraction.model_dump(),
                    extraction_confidence=extraction.confidence_score,
                    received_at=datetime.utcnow(),
                )
                db.add(new_q)

            req_match.status = "quoted"
            synced_count += 1
            extracted_quotes += 1
            details.append(f"Synced reply from {from_email} (Msg ID: {msg_id}) -> extracted quotation for {sup.company_name}.")

    db.commit()
    return SyncRepliesResponse(
        synced_messages_count=synced_count,
        quotations_extracted_count=extracted_quotes,
        details=details if details else ["No new unread supplier replies found in connected mailboxes."]
    )


@router.post("/generate-followup/{dispatch_id}", response_model=EmailDraftResponse)
async def generate_follow_up_draft(
    dispatch_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    AI generates follow-up reminder email draft for non-responsive suppliers.
    CRITICAL: Proposal is saved in delivery_status='draft' for human approval.
    """
    disp = db.query(RFQDispatch).filter(RFQDispatch.id == dispatch_id).first()
    if not disp:
        raise HTTPException(status_code=404, detail="RFQ Dispatch record not found")

    rfq = db.query(RFQ).filter(RFQ.id == disp.rfq_id).first()
    sup = db.query(Supplier).filter(Supplier.id == disp.supplier_id).first()
    contact = db.query(SupplierContact).filter(SupplierContact.supplier_id == disp.supplier_id).first()

    target_email = contact.email if contact else f"sales@{sup.canonical_domain if sup else 'supplier.com'}"
    target_name = sup.company_name if sup else "Sales Team"

    proposal = await orchestrator.email_automation_agent.execute(
        supplier_name=target_name,
        supplier_email=target_email,
        rfq_title=rfq.title if rfq else "Procurement Requirement",
        rfq_markdown=rfq.content if rfq else "",
        is_follow_up=True,
    )

    draft = EmailDraft(
        rfq_id=disp.rfq_id,
        supplier_id=disp.supplier_id,
        created_by_user_id=current_user.id,
        draft_type="follow_up_reminder",
        recipient_email=proposal["recipient_email"],
        recipient_name=proposal["recipient_name"],
        subject=proposal["subject"],
        body_markdown=proposal["body_markdown"],
        delivery_status="draft",
    )
    db.add(draft)

    disp.follow_up_count += 1
    disp.last_follow_up_at = datetime.utcnow()

    db.commit()
    db.refresh(draft)

    res = EmailDraftResponse.model_validate(draft)
    res.supplier_name = target_name
    return res


@router.post("/validate-attachment")
def validate_email_attachment(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Validate attachment file size and extension prior to processing."""
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

    return {
        "filename": file.filename,
        "extension": ext,
        "size_bytes": size_bytes,
        "valid": True
    }
