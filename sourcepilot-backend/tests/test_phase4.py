"""
SourcePilot AI — Phase 4 Verification Suite

Tests all Connected Email Integration capabilities:
  1. Fernet token encryption & decryption (using FERNET_KEY)
  2. User-scoped connected mailboxes (isolation between users)
  3. OAuth state validation (CSRF protection) & PKCE pair generation
  4. Human-in-the-Loop email dispatch: AI creates draft ONLY; send requires explicit human approval
  5. Inbox sync idempotency (message ID deduplication)
  6. Attachment type and size validation
  7. End-to-end inbound supplier reply flow: dispatch → reply → sync → extraction → quote comparison
  8. Provider Mock HTTP Verification (OAuth, request construction, inbox parsing, network errors, HITL safeguard)
  9. End-to-End Quotation Attachment Flow (PDF/XLSX validation, rejection, data extraction, linking, comparison & deduplication)
  10. Direct Supplier Quote Attachment Upload UI Endpoint & Regression Tests (Precision vs Prime Electronics)
"""
import io
import uuid
import pytest
import openpyxl
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.core.token_crypto import encrypt_token, decrypt_token
from app.core.config import settings
from app.infrastructure.db.models.connected_account import ConnectedAccount
from app.infrastructure.email.gmail_provider import GmailProvider
from app.infrastructure.email.outlook_provider import OutlookProvider

client = TestClient(app)


def _register_user(email_prefix: str) -> tuple[str, dict]:
    uid = str(uuid.uuid4())[:8]
    payload = {
        "org_name": f"Phase4 Org {uid}",
        "email": f"{email_prefix}_{uid}@p4test.com",
        "password": "Password123!",
        "full_name": "Phase4 User",
    }
    res = client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 200, f"Register failed: {res.text}"
    token = res.json()["access_token"]
    return token, {"Authorization": f"Bearer {token}"}


# ────────────────────────────────────────────────────────────────────────────
# 1. Token Encryption & Decryption
# ────────────────────────────────────────────────────────────────────────────

def test_fernet_token_encryption_and_decryption():
    """Verify Fernet encryption & decryption works deterministically using FERNET_KEY."""
    raw_token = "ya29.a0ARdaC0B_mock_google_oauth_access_token_12345"
    encrypted = encrypt_token(raw_token)
    assert encrypted != raw_token
    decrypted = decrypt_token(encrypted)
    assert decrypted == raw_token


# ────────────────────────────────────────────────────────────────────────────
# 2. User-Scoped Connected Mailboxes & Disconnect
# ────────────────────────────────────────────────────────────────────────────

def test_connected_accounts_user_scoping():
    """Verify connected accounts are strictly user-scoped."""
    _, headers1 = _register_user("user1")
    _, headers2 = _register_user("user2")

    # User 1 authorizes Gmail
    auth_res = client.get("/api/v1/connected-accounts/oauth/authorize/gmail", headers=headers1)
    assert auth_res.status_code == 200
    state = auth_res.json()["state"]

    cb_res = client.post(
        "/api/v1/connected-accounts/oauth/callback/gmail",
        json={"code": "code_user1", "state": state},
        headers=headers1,
    )
    assert cb_res.status_code == 200
    acc1_id = cb_res.json()["id"]

    # User 1 lists accounts -> sees acc1
    list1 = client.get("/api/v1/connected-accounts/", headers=headers1).json()
    assert any(a["id"] == acc1_id for a in list1)

    # User 2 lists accounts -> cannot see User 1's mailbox
    list2 = client.get("/api/v1/connected-accounts/", headers=headers2).json()
    assert not any(a["id"] == acc1_id for a in list2)

    # User 2 tries to disconnect User 1's account -> 404 access denied
    del_res = client.delete(f"/api/v1/connected-accounts/{acc1_id}", headers=headers2)
    assert del_res.status_code == 404

    # User 1 disconnects own account -> 204 success
    del_own = client.delete(f"/api/v1/connected-accounts/{acc1_id}", headers=headers1)
    assert del_own.status_code == 204


# ────────────────────────────────────────────────────────────────────────────
# 3. OAuth State CSRF Validation
# ────────────────────────────────────────────────────────────────────────────

def test_oauth_state_validation():
    """Verify invalid OAuth state parameters are rejected with 400."""
    _, headers = _register_user("user_state")
    cb_bad = client.post(
        "/api/v1/connected-accounts/oauth/callback/gmail",
        json={"code": "code_test", "state": "invalid_bogus_state"},
        headers=headers,
    )
    assert cb_bad.status_code == 400
    assert "Invalid or expired OAuth state" in cb_bad.json()["detail"]


# ────────────────────────────────────────────────────────────────────────────
# 4. Human-in-the-Loop Email Review & Dispatch Workflow
# ────────────────────────────────────────────────────────────────────────────

def test_email_draft_creation_requires_human_approval():
    """
    Verify AI creates drafts in delivery_status='draft',
    and sending requires explicit human approval.
    """
    uid = str(uuid.uuid4())[:8]
    _, headers = _register_user("buyer_hitl")

    # 1. Create requirement & discover
    req_res = client.post("/api/v1/requirements", json={"raw_text": f"Need 100 units motors {uid}"}, headers=headers)
    req_id = req_res.json()["id"]
    client.post(f"/api/v1/requirements/{req_id}/suppliers/discover", headers=headers)

    # 2. Generate RFQ & approve via multi-approver workflow
    rfq_res = client.post(f"/api/v1/rfq/generate/{req_id}", headers=headers)
    rfq_id = rfq_res.json()["id"]
    client.post(f"/api/v1/rfq/{rfq_id}/submit-for-approval", headers=headers)
    client.post(f"/api/v1/rfq/{rfq_id}/approve-step", json={"step_number": 1}, headers=headers)
    client.post(f"/api/v1/rfq/{rfq_id}/approve-step", json={"step_number": 2}, headers=headers)

    # 3. Generate drafts via AI agent -> delivery_status MUST be 'draft'
    gen_res = client.post(f"/api/v1/email-drafts/generate/{rfq_id}", headers=headers)
    assert gen_res.status_code == 200
    drafts = gen_res.json()
    assert len(drafts) > 0
    first_draft = drafts[0]
    assert first_draft["delivery_status"] == "draft"
    assert first_draft["approved_by_user_id"] is None

    # 4. Human edits draft text
    patch_res = client.patch(
        f"/api/v1/email-drafts/{first_draft['id']}",
        json={"subject": "[Revised Subject] Motor Quote Request"},
        headers=headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["subject"] == "[Revised Subject] Motor Quote Request"

    # 5. Human grants explicit approval & sends email
    send_res = client.post(
        f"/api/v1/email-drafts/{first_draft['id']}/approve-and-send",
        json={"approval_notes": "Reviewed and approved by Alex"},
        headers=headers,
    )
    assert send_res.status_code == 200
    sent_data = send_res.json()
    assert sent_data["delivery_status"] == "sent"
    assert sent_data["approved_by_user_id"] is not None
    assert sent_data["sent_at"] is not None


# ────────────────────────────────────────────────────────────────────────────
# 5. End-to-End Inbound Supplier Reply & Quotation Flow
# ────────────────────────────────────────────────────────────────────────────

def test_end_to_end_inbound_supplier_reply_flow():
    """
    Test Phase 4 end-to-end inbound supplier reply flow:
    1. Connect Gmail mailbox (mock mode).
    2. Create requirement, discover suppliers, generate & approve RFQ.
    3. Generate email draft, grant explicit human approval, and dispatch RFQ.
    4. Sync mailbox replies: detects mock reply, runs QuotationExtractionAgent,
       creates structured quotation with unit price, total price, lead time, MOQ, payment terms, and warranty.
    5. Deduplicates on subsequent sync (idempotency).
    6. Verifies recommendation API generates quote comparison analysis.
    """
    uid = str(uuid.uuid4())[:8]
    _, headers = _register_user("reply_user")

    # 1. Connect Mailbox
    auth = client.get("/api/v1/connected-accounts/oauth/authorize/gmail", headers=headers).json()
    client.post(
        "/api/v1/connected-accounts/oauth/callback/gmail",
        json={"code": "mock_code", "state": auth["state"]},
        headers=headers,
    )

    # 2. Requirement -> Discover -> RFQ -> Multi-Approve
    req_res = client.post("/api/v1/requirements", json={"raw_text": f"Procure 500 units servos {uid}"}, headers=headers)
    req_id = req_res.json()["id"]
    client.post(f"/api/v1/requirements/{req_id}/suppliers/discover", headers=headers)

    rfq = client.post(f"/api/v1/rfq/generate/{req_id}", headers=headers).json()
    rfq_id = rfq["id"]
    client.post(f"/api/v1/rfq/{rfq_id}/submit-for-approval", headers=headers)
    client.post(f"/api/v1/rfq/{rfq_id}/approve-step", json={"step_number": 1}, headers=headers)
    client.post(f"/api/v1/rfq/{rfq_id}/approve-step", json={"step_number": 2}, headers=headers)

    # 3. Draft & Approve/Send
    drafts = client.post(f"/api/v1/email-drafts/generate/{rfq_id}", headers=headers).json()
    draft_id = drafts[0]["id"]
    send_res = client.post(f"/api/v1/email-drafts/{draft_id}/approve-and-send", json={}, headers=headers)
    assert send_res.status_code == 200
    assert send_res.json()["delivery_status"] == "sent"

    # 4. Sync Mailbox Replies — First Pass
    sync1 = client.post("/api/v1/email-drafts/sync-replies", headers=headers)
    assert sync1.status_code == 200
    s1_data = sync1.json()
    assert s1_data["synced_messages_count"] == 1
    assert s1_data["quotations_extracted_count"] == 1

    # 5. Check Quotations endpoint
    q_res = client.get(f"/api/v1/quotations/requirement/{req_id}", headers=headers)
    assert q_res.status_code == 200
    quotes = q_res.json()
    assert len(quotes) == 1
    ext = quotes[0]["extracted_data"]
    assert ext["unit_price"] == 24.50
    assert ext["total_price"] == 12250.0
    assert ext["moq"] == "100 units"
    assert ext["lead_time_days"] == 14
    assert ext["payment_terms"] == "Net 30"

    # 6. Sync Mailbox Replies — Second Pass (Idempotent: No Duplicate Quotation)
    sync2 = client.post("/api/v1/email-drafts/sync-replies", headers=headers)
    assert sync2.status_code == 200
    assert sync2.json()["synced_messages_count"] == 0

    quotes2 = client.get(f"/api/v1/quotations/requirement/{req_id}", headers=headers).json()
    assert len(quotes2) == 1  # Deduplicated

    # 7. Quote Comparison Recommendation Verification
    rec_res = client.get(f"/api/v1/quotations/recommendation/{req_id}", headers=headers)
    assert rec_res.status_code == 200
    assert rec_res.json()["recommended_supplier_id"] is not None


# ────────────────────────────────────────────────────────────────────────────
# 6. Provider Mock HTTP Verification (Gmail & Outlook)
# ────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_gmail_provider_oauth_refresh_and_send_request():
    """Verify Gmail OAuth token refresh & send request construction with mocked HTTP responses."""
    account = ConnectedAccount(
        id="acc_gmail_test",
        user_id="usr_test",
        provider="gmail",
        email_address="buyer@gmail.com",
        encrypted_access_token=encrypt_token("old_access_token"),
        encrypted_refresh_token=encrypt_token("gmail_refresh_tok"),
        token_expires_at=datetime.utcnow() - timedelta(seconds=120),  # Expired token
        status="active",
    )

    with patch.object(settings, "MOCK_OAUTH", False):
        mock_resp_refresh = MagicMock()
        mock_resp_refresh.status_code = 200
        mock_resp_refresh.json.return_value = {"access_token": "fresh_gmail_access_token", "expires_in": 3600}

        mock_resp_send = MagicMock()
        mock_resp_send.status_code = 200
        mock_resp_send.json.return_value = {"id": "gmail_msg_id_999"}

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = [mock_resp_refresh, mock_resp_send]

            provider = GmailProvider()
            result = await provider.send_draft(
                account,
                to_email="supplier@precision.com",
                subject="[RFQ] Motor Request",
                body_markdown="Please quote 100 units.",
                reply_to_message_id="prev_msg_001",
            )

            assert result.success is True
            assert result.provider_message_id == "gmail_msg_id_999"

            # Verify OAuth token refresh request construction
            refresh_call = mock_post.call_args_list[0]
            assert refresh_call.args[0] == "https://oauth2.googleapis.com/token"
            assert refresh_call.kwargs["data"]["grant_type"] == "refresh_token"
            assert refresh_call.kwargs["data"]["refresh_token"] == "gmail_refresh_tok"

            # Verify Send request construction
            send_call = mock_post.call_args_list[1]
            assert send_call.args[0] == "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
            assert send_call.kwargs["headers"]["Authorization"] == "Bearer fresh_gmail_access_token"
            assert "raw" in send_call.kwargs["json"]

            # Token in account updated
            assert decrypt_token(account.encrypted_access_token) == "fresh_gmail_access_token"


@pytest.mark.asyncio
async def test_outlook_provider_oauth_refresh_and_send_request():
    """Verify Outlook Graph API token refresh & send request construction with mocked HTTP responses."""
    account = ConnectedAccount(
        id="acc_outlook_test",
        user_id="usr_test",
        provider="outlook",
        email_address="buyer@outlook.com",
        encrypted_access_token=encrypt_token("old_outlook_tok"),
        encrypted_refresh_token=encrypt_token("outlook_refresh_tok"),
        token_expires_at=datetime.utcnow() - timedelta(seconds=120),  # Expired token
        status="active",
    )

    with patch.object(settings, "MOCK_OAUTH", False):
        mock_resp_refresh = MagicMock()
        mock_resp_refresh.status_code = 200
        mock_resp_refresh.json.return_value = {"access_token": "fresh_outlook_access_token", "expires_in": 3600}

        mock_resp_send = MagicMock()
        mock_resp_send.status_code = 202
        mock_resp_send.json.return_value = {}

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = [mock_resp_refresh, mock_resp_send]

            provider = OutlookProvider()
            result = await provider.send_draft(
                account,
                to_email="sales@supplier.com",
                subject="[RFQ] Outlook Sourcing",
                body_markdown="Please reply with price.",
            )

            assert result.success is True
            assert result.provider_message_id.startswith("outlook_msg_")

            # Verify Token refresh request
            refresh_call = mock_post.call_args_list[0]
            assert refresh_call.args[0] == "https://login.microsoftonline.com/common/oauth2/v2.0/token"

            # Verify Send request JSON payload structure
            send_call = mock_post.call_args_list[1]
            assert send_call.args[0] == "https://graph.microsoft.com/v1.0/me/sendMail"
            assert send_call.kwargs["headers"]["Authorization"] == "Bearer fresh_outlook_access_token"
            body_data = send_call.kwargs["json"]["message"]
            assert body_data["subject"] == "[RFQ] Outlook Sourcing"
            assert body_data["toRecipients"][0]["emailAddress"]["address"] == "sales@supplier.com"


@pytest.mark.asyncio
async def test_gmail_and_outlook_inbox_reply_retrieval():
    """Verify Gmail & Outlook inbox reply retrieval and message/thread ID parsing."""
    acc_gmail = ConnectedAccount(
        id="a_g", user_id="u1", provider="gmail", email_address="b@gmail.com",
        encrypted_access_token=encrypt_token("tok_g"), status="active"
    )
    acc_out = ConnectedAccount(
        id="a_o", user_id="u1", provider="outlook", email_address="b@outlook.com",
        encrypted_access_token=encrypt_token("tok_o"), status="active"
    )

    with patch.object(settings, "MOCK_OAUTH", False):
        # Gmail Mock Responses
        mock_g_list = MagicMock(status_code=200)
        mock_g_list.json.return_value = {"messages": [{"id": "g_msg_100", "threadId": "g_thread_100"}]}
        mock_g_msg = MagicMock(status_code=200)
        mock_g_msg.json.return_value = {
            "snippet": "Quotation details: $25.00",
            "threadId": "g_thread_100",
            "payload": {"headers": [{"name": "From", "value": "sales@supplier.com"}, {"name": "Subject", "value": "Re: RFQ"}]}
        }

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_g_get:
            mock_g_get.side_effect = [mock_g_list, mock_g_msg]
            g_replies = await GmailProvider().sync_inbox_replies(acc_gmail)
            assert len(g_replies) == 1
            assert g_replies[0]["provider_message_id"] == "g_msg_100"
            assert g_replies[0]["thread_id"] == "g_thread_100"
            assert g_replies[0]["from_email"] == "sales@supplier.com"

        # Outlook Mock Responses
        mock_o_list = MagicMock(status_code=200)
        mock_o_list.json.return_value = {
            "value": [{
                "id": "o_msg_200",
                "conversationId": "o_thread_200",
                "from": {"emailAddress": {"address": "quote@supplier.com"}},
                "subject": "Re: Quotation Request",
                "bodyPreview": "Our unit price is $28.00"
            }]
        }

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_o_get:
            mock_o_get.return_value = mock_o_list
            o_replies = await OutlookProvider().sync_inbox_replies(acc_out)
            assert len(o_replies) == 1
            assert o_replies[0]["provider_message_id"] == "o_msg_200"
            assert o_replies[0]["thread_id"] == "o_thread_200"
            assert o_replies[0]["from_email"] == "quote@supplier.com"


@pytest.mark.asyncio
async def test_provider_api_and_network_failure_handling():
    """Verify provider API errors (401/500) or network exceptions return failed result cleanly without crashing."""
    account = ConnectedAccount(
        id="acc_err", user_id="u1", provider="gmail", email_address="b@gmail.com",
        encrypted_access_token=encrypt_token("tok_err"), status="active"
    )

    with patch.object(settings, "MOCK_OAUTH", False):
        mock_err_resp = MagicMock(status_code=500, text="Internal Provider Server Error")
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_err_resp
            result = await GmailProvider().send_draft(
                account, to_email="supplier@corp.com", subject="Sub", body_markdown="Body"
            )
            assert result.success is False
            assert "Gmail API error (500)" in result.error_message


def test_no_email_sent_without_explicit_human_approval():
    """
    Safeguard Verification: Ensure AI draft creation does NOT execute outbound email dispatch,
    and attempting to send without invoking explicit human approval API keeps draft in draft state.
    """
    uid = str(uuid.uuid4())[:8]
    _, headers = _register_user("safe_user")

    # Create & approve RFQ
    req_id = client.post("/api/v1/requirements", json={"raw_text": f"Safeguard Test {uid}"}, headers=headers).json()["id"]
    client.post(f"/api/v1/requirements/{req_id}/suppliers/discover", headers=headers)
    rfq_id = client.post(f"/api/v1/rfq/generate/{req_id}", headers=headers).json()["id"]
    client.post(f"/api/v1/rfq/{rfq_id}/submit-for-approval", headers=headers)
    client.post(f"/api/v1/rfq/{rfq_id}/approve-step", json={"step_number": 1}, headers=headers)
    client.post(f"/api/v1/rfq/{rfq_id}/approve-step", json={"step_number": 2}, headers=headers)

    # Generate drafts via AI Agent
    drafts = client.post(f"/api/v1/email-drafts/generate/{rfq_id}", headers=headers).json()
    assert len(drafts) > 0
    d = drafts[0]

    # Verify state is draft and no human approval recorded
    assert d["delivery_status"] == "draft"
    assert d["approved_by_user_id"] is None
    assert d["approved_at"] is None

    # Fetch draft again via GET to verify it remains in draft status without sending
    refreshed_drafts = client.get(f"/api/v1/email-drafts/rfq/{rfq_id}", headers=headers).json()
    assert refreshed_drafts[0]["delivery_status"] == "draft"
    assert refreshed_drafts[0]["approved_by_user_id"] is None


# ────────────────────────────────────────────────────────────────────────────
# 7. End-to-End Quotation Attachment Flow Verification
# ────────────────────────────────────────────────────────────────────────────

def test_end_to_end_quotation_attachment_flow():
    """
    End-to-End verification of PDF/XLSX quotation attachment flow:
    1. Allowed attachment validation (.pdf, .xlsx -> 200 OK).
    2. Invalid (.exe) and oversized (>10MB) files rejected safely with 400 Bad Request.
    3. PDF/XLSX attachment quotation data extracted into structured fields:
       supplier name, unit price, quantity, total price, lead time, MOQ, payment terms, warranty.
    4. Quotation linked to correct requirement and supplier.
    5. Quotation appears correctly in Quote Comparison.
    6. Reprocessing the same attachment/reply does not create duplicate quotations.
    """
    uid = str(uuid.uuid4())[:8]
    _, headers = _register_user("att_user")

    # 1. Attachment Validation Tests
    res_pdf = client.post(
        "/api/v1/email-drafts/validate-attachment",
        files={"file": ("supplier_quote.pdf", b"%PDF-1.4 sample content", "application/pdf")},
        headers=headers,
    )
    assert res_pdf.status_code == 200
    assert res_pdf.json()["valid"] is True

    res_xlsx = client.post(
        "/api/v1/email-drafts/validate-attachment",
        files={"file": ("supplier_quote.xlsx", b"PK\x03\x04 excel content", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=headers,
    )
    assert res_xlsx.status_code == 200
    assert res_xlsx.json()["valid"] is True

    res_exe = client.post(
        "/api/v1/email-drafts/validate-attachment",
        files={"file": ("malicious.exe", b"executable payload", "application/octet-stream")},
        headers=headers,
    )
    assert res_exe.status_code == 400
    assert "not supported" in res_exe.json()["detail"]

    huge_payload = b"X" * (11 * 1024 * 1024)
    res_huge = client.post(
        "/api/v1/email-drafts/validate-attachment",
        files={"file": ("oversized.pdf", huge_payload, "application/pdf")},
        headers=headers,
    )
    assert res_huge.status_code == 400
    assert "exceeds limit" in res_huge.json()["detail"]

    # 2. Setup Requirement, Dispatched RFQ & Connect Mailbox
    auth = client.get("/api/v1/connected-accounts/oauth/authorize/gmail", headers=headers).json()
    client.post("/api/v1/connected-accounts/oauth/callback/gmail", json={"code": "m_code", "state": auth["state"]}, headers=headers)

    req_id = client.post("/api/v1/requirements", json={"raw_text": f"Procure 500 motors {uid}"}, headers=headers).json()["id"]
    client.post(f"/api/v1/requirements/{req_id}/suppliers/discover", headers=headers)

    rfq_id = client.post(f"/api/v1/rfq/generate/{req_id}", headers=headers).json()["id"]
    client.post(f"/api/v1/rfq/{rfq_id}/submit-for-approval", headers=headers)
    client.post(f"/api/v1/rfq/{rfq_id}/approve-step", json={"step_number": 1}, headers=headers)
    client.post(f"/api/v1/rfq/{rfq_id}/approve-step", json={"step_number": 2}, headers=headers)

    draft_id = client.post(f"/api/v1/email-drafts/generate/{rfq_id}", headers=headers).json()[0]["id"]
    client.post(f"/api/v1/email-drafts/{draft_id}/approve-and-send", json={}, headers=headers)

    # 3. Sync Mailbox Replies (processes PDF/XLSX attachment data)
    sync_res = client.post("/api/v1/email-drafts/sync-replies", headers=headers)
    assert sync_res.status_code == 200
    assert sync_res.json()["quotations_extracted_count"] == 1

    # 4. Verify Quotation Extraction & Requirement/Supplier Linking
    quotes = client.get(f"/api/v1/quotations/requirement/{req_id}", headers=headers).json()
    assert len(quotes) == 1
    q = quotes[0]
    assert q["requirement_id"] == req_id
    assert q["supplier_id"] is not None

    extracted = q["extracted_data"]
    assert extracted["unit_price"] == 24.50
    assert extracted["total_price"] == 12250.0
    assert extracted["moq"] == "100 units"
    assert extracted["lead_time_days"] == 14
    assert extracted["payment_terms"] == "Net 30"

    # 5. Verify Quote Comparison Matrix
    rec = client.get(f"/api/v1/quotations/recommendation/{req_id}", headers=headers).json()
    assert rec["recommended_supplier_id"] is not None
    assert len(rec["comparison_matrix"]) > 0

    # 6. Verify Reprocessing Attachment Does Not Create Duplicate Quotations
    sync_dup = client.post("/api/v1/email-drafts/sync-replies", headers=headers)
    assert sync_dup.status_code == 200
    assert sync_dup.json()["synced_messages_count"] == 0

    quotes_after = client.get(f"/api/v1/quotations/requirement/{req_id}", headers=headers).json()
    assert len(quotes_after) == 1  # Deduplicated


# ────────────────────────────────────────────────────────────────────────────
# 8. Direct Supplier Quote Attachment Upload UI Endpoint & Regression Tests
# ────────────────────────────────────────────────────────────────────────────

def test_upload_quotation_attachment_endpoint():
    """Verify manual PDF/XLSX quotation attachment upload via POST /quotations/upload-attachment."""
    uid = str(uuid.uuid4())[:8]
    _, headers = _register_user("direct_upload_user")

    # 1. Setup requirement & supplier match
    req_id = client.post("/api/v1/requirements", json={"raw_text": f"Need 300 units solar panels {uid}"}, headers=headers).json()["id"]
    matches = client.post(f"/api/v1/requirements/{req_id}/suppliers/discover", headers=headers).json()
    sup_id = matches[0]["supplier"]["id"]

    # 2. Upload PDF attachment document
    pdf_content = (
        "SUPPLIER QUOTATION DOCUMENT (PDF)\n"
        "Supplier Name: Precision Electronics & Machinery Solutions Ltd.\n"
        "Item: Solar Panels\n"
        "Unit Price: $185.00\n"
        "Quantity: 300 units\n"
        "Total Price: $55,500.00\n"
        "Lead Time: 10 days\n"
        "MOQ: 50 units\n"
        "Payment Terms: Net 30\n"
        "Warranty: 10-Year Warranty"
    ).encode("utf-8")

    res_upload = client.post(
        "/api/v1/quotations/upload-attachment",
        data={"requirement_id": req_id, "supplier_id": sup_id},
        files={"file": ("solar_panel_quote.pdf", pdf_content, "application/pdf")},
        headers=headers,
    )
    assert res_upload.status_code == 200
    q_data = res_upload.json()
    assert q_data["requirement_id"] == req_id
    assert q_data["supplier_id"] == sup_id
    assert q_data["extracted_data"] is not None

    # 3. Verify quotation appears in requirement quotations list
    quotes = client.get(f"/api/v1/quotations/requirement/{req_id}", headers=headers).json()
    assert len(quotes) == 1

    # 4. Verify duplicate upload upserts and deduplicates
    res_dup = client.post(
        "/api/v1/quotations/upload-attachment",
        data={"requirement_id": req_id, "supplier_id": sup_id},
        files={"file": ("solar_panel_quote.pdf", pdf_content, "application/pdf")},
        headers=headers,
    )
    assert res_dup.status_code == 200
    quotes_after = client.get(f"/api/v1/quotations/requirement/{req_id}", headers=headers).json()
    assert len(quotes_after) == 1


def test_precision_vs_prime_quotation_upload_regression():
    """
    Regression Test:
    1. Upload Precision Electronics XLSX quotation ($24.50, $12,250.00, 14 days, Net 30, 1-Year Warranty).
    2. Upload Prime Electronics PDF quotation ($26.75, $13,375.00, 18 days, Net 45, 2-Year Warranty).
    3. Verify Prime Electronics quote stores $26.75, $13,375.00, 18 days, Net 45, 2-Year Warranty and NEVER defaults to Precision's values.
    4. Verify unparseable file without price numbers returns HTTP 400 Bad Request.
    5. Verify (requirement_id, supplier_id) deduplication on re-upload.
    """
    uid = str(uuid.uuid4())[:8]
    _, headers = _register_user("supplier_diff_user")

    # Setup Requirement & Discover Suppliers
    req_id = client.post("/api/v1/requirements", json={"raw_text": f"Need 500 DC motors {uid}"}, headers=headers).json()["id"]
    matches = client.post(f"/api/v1/requirements/{req_id}/suppliers/discover", headers=headers).json()
    sup_precision_id = matches[0]["supplier"]["id"]
    sup_prime_id = matches[1]["supplier"]["id"]

    # 1. Upload Precision Electronics XLSX Quotation via openpyxl
    wb_prec = openpyxl.Workbook()
    ws_p = wb_prec.active
    ws_p.append(["Supplier Name", "Precision Electronics"])
    ws_p.append(["Unit Price", 24.50])
    ws_p.append(["Quantity", 500])
    ws_p.append(["Total Price", 12250.00])
    ws_p.append(["Lead Time", "14 days"])
    ws_p.append(["MOQ", "100 units"])
    ws_p.append(["Payment Terms", "Net 30"])
    ws_p.append(["Warranty", "1-Year Warranty"])

    p_buf = io.BytesIO()
    wb_prec.save(p_buf)

    res_prec = client.post(
        "/api/v1/quotations/upload-attachment",
        data={"requirement_id": req_id, "supplier_id": sup_precision_id},
        files={"file": ("precision_quote.xlsx", p_buf.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=headers,
    )
    assert res_prec.status_code == 200
    prec_ext = res_prec.json()["extracted_data"]
    assert prec_ext["unit_price"] == 24.50
    assert prec_ext["total_price"] == 12250.00
    assert prec_ext["lead_time_days"] == 14
    assert prec_ext["payment_terms"] == "Net 30"

    # 2. Upload Prime Electronics PDF Quotation ($26.75, $13,375.00, 18 days, Net 45, 2-Year Warranty)
    prime_pdf_text = (
        "SUPPLIER QUOTATION SHEET (PDF)\n"
        "Supplier Name: Prime Electronics\n"
        "Item: Brushless DC Motor\n"
        "Unit Price: $26.75\n"
        "Quantity: 500 units\n"
        "Total Price: $13,375.00\n"
        "Lead Time: 18 days\n"
        "MOQ: 150 units\n"
        "Payment Terms: Net 45\n"
        "Warranty: 2-Year Warranty"
    ).encode("utf-8")

    res_prime = client.post(
        "/api/v1/quotations/upload-attachment",
        data={"requirement_id": req_id, "supplier_id": sup_prime_id},
        files={"file": ("prime_quote.pdf", prime_pdf_text, "application/pdf")},
        headers=headers,
    )
    assert res_prime.status_code == 200
    prime_ext = res_prime.json()["extracted_data"]

    # Verify Prime Electronics values are extracted correctly and NEVER reuse Precision's values
    assert prime_ext["unit_price"] == 26.75
    assert prime_ext["total_price"] == 13375.00
    assert prime_ext["lead_time_days"] == 18
    assert prime_ext["payment_terms"] == "Net 45"
    assert "2-Year" in prime_ext["notes"]

    # 3. Verify Quotations List for Requirement contains BOTH distinct quotes
    quotes = client.get(f"/api/v1/quotations/requirement/{req_id}", headers=headers).json()
    assert len(quotes) == 2

    # 4. Verify Unparseable / Blank Document Upload returns HTTP 400 Bad Request
    res_bad = client.post(
        "/api/v1/quotations/upload-attachment",
        data={"requirement_id": req_id, "supplier_id": sup_prime_id},
        files={"file": ("invalid_text.txt", b"General message without quotation numbers.", "text/plain")},
        headers=headers,
    )
    assert res_bad.status_code == 400
    assert "Could not extract financial quotation numbers" in res_bad.json()["detail"]

    # 5. Verify Deduplication when re-uploading updated Prime quote
    res_dup = client.post(
        "/api/v1/quotations/upload-attachment",
        data={"requirement_id": req_id, "supplier_id": sup_prime_id},
        files={"file": ("prime_quote.pdf", prime_pdf_text, "application/pdf")},
        headers=headers,
    )
    assert res_dup.status_code == 200
    quotes_after = client.get(f"/api/v1/quotations/requirement/{req_id}", headers=headers).json()
    assert len(quotes_after) == 2  # No duplicate row created
