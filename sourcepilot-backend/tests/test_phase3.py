"""
SourcePilot AI — Phase 3 Automated Verification Suite

Tests all new Phase 3 capabilities:
  1. Real Supplier Discovery (Bing connector registered)
  2. Saved Supplier Library (save, list, delete, attach-to-requirement)
  3. Price Trend Analytics endpoint
  4. Market Intelligence Agent endpoint
  5. Supplier Risk Analysis (multi-dimensional risk via supplier intelligence agent)
  6. Multi-Approver RFQ Workflow (submit-for-approval, approve-step, reject-step)
"""
import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.infrastructure.search_connectors.connector_registry import connector_registry

client = TestClient(app)


# ────────────────────────────────────────────────────────────────────────────
# Helper fixtures
# ────────────────────────────────────────────────────────────────────────────

def _register_and_token(uid: str) -> tuple[str, dict]:
    """Register a fresh org/user and return (user_id, auth_headers)."""
    payload = {
        "org_name": f"Phase3 Org {uid}",
        "email": f"buyer_{uid}@phase3corp.com",
        "password": "TestPassword123!",
        "full_name": "Phase3 Buyer",
    }
    res = client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 200, f"Register failed: {res.text}"
    token = res.json()["access_token"]
    return token, {"Authorization": f"Bearer {token}"}


def _create_requirement(headers: dict, uid: str) -> str:
    res = client.post(
        "/api/v1/requirements",
        json={"raw_text": f"Need 500 units ISO 9001 certified stainless steel flanges for chemical plant {uid}."},
        headers=headers,
    )
    assert res.status_code == 200, f"Create requirement failed: {res.text}"
    return res.json()["id"]


def _discover_suppliers(headers: dict, req_id: str) -> list:
    res = client.post(f"/api/v1/requirements/{req_id}/suppliers/discover", headers=headers)
    assert res.status_code == 200, f"Discovery failed: {res.text}"
    matches = res.json()
    assert len(matches) > 0, "Discovery returned no suppliers"
    return matches


def _generate_rfq(headers: dict, req_id: str) -> str:
    res = client.post(f"/api/v1/rfq/generate/{req_id}", headers=headers)
    assert res.status_code == 200, f"RFQ generation failed: {res.text}"
    return res.json()["id"]


# ────────────────────────────────────────────────────────────────────────────
# 1. Real Supplier Discovery — Bing connector registered
# ────────────────────────────────────────────────────────────────────────────

def test_bing_connector_registered():
    """Verify BingSearchConnector is registered in the connector registry."""
    names = connector_registry.list_connector_names()
    assert "bing_search" in names, (
        f"'bing_search' not found in registry. Registered: {names}"
    )


def test_discovery_returns_enriched_suppliers():
    """End-to-end: discover suppliers and verify required fields are present."""
    uid = str(uuid.uuid4())[:8]
    _, headers = _register_and_token(uid)
    req_id = _create_requirement(headers, uid)
    matches = _discover_suppliers(headers, req_id)

    first = matches[0]
    supplier = first.get("supplier", {})

    assert "id" in supplier
    assert "company_name" in supplier
    assert first.get("rank_score") is not None
    assert first.get("rank_explanation") is not None


# ────────────────────────────────────────────────────────────────────────────
# 2. Saved Supplier Library
# ────────────────────────────────────────────────────────────────────────────

def test_saved_supplier_library_crud():
    """Save, list, update, and delete a supplier from the library."""
    uid = str(uuid.uuid4())[:8]
    _, headers = _register_and_token(uid)
    req_id = _create_requirement(headers, uid)
    matches = _discover_suppliers(headers, req_id)
    supplier_id = matches[0]["supplier"]["id"]

    # 1. Save supplier to library
    save_res = client.post(
        "/api/v1/saved-suppliers/",
        json={
            "supplier_id": supplier_id,
            "category": "Industrial Metals",
            "status": "preferred",
            "tags": ["iso-9001", "stainless-steel"],
            "notes": "Reliable delivery in Q2 2026",
        },
        headers=headers,
    )
    assert save_res.status_code == 201, f"Save failed: {save_res.text}"
    saved = save_res.json()
    assert saved["supplier_id"] == supplier_id
    assert saved["category"] == "Industrial Metals"
    assert saved["status"] == "preferred"

    # 2. List library — should include saved entry
    list_res = client.get("/api/v1/saved-suppliers/", headers=headers)
    assert list_res.status_code == 200
    library = list_res.json()
    assert any(s["supplier_id"] == supplier_id for s in library)

    # 3. Filter by category
    cat_res = client.get("/api/v1/saved-suppliers/?category=Industrial+Metals", headers=headers)
    assert cat_res.status_code == 200
    assert len(cat_res.json()) >= 1

    # 4. Save again (upsert) with updated notes
    upsert_res = client.post(
        "/api/v1/saved-suppliers/",
        json={
            "supplier_id": supplier_id,
            "category": "Industrial Metals",
            "status": "approved",
            "notes": "Approved after compliance review",
        },
        headers=headers,
    )
    assert upsert_res.status_code == 201
    assert upsert_res.json()["status"] == "approved"

    # 5. Delete from library
    del_res = client.delete(f"/api/v1/saved-suppliers/{supplier_id}", headers=headers)
    assert del_res.status_code == 204

    # 6. Confirm deletion
    list_after = client.get("/api/v1/saved-suppliers/", headers=headers)
    assert not any(s["supplier_id"] == supplier_id for s in list_after.json())


def test_attach_saved_suppliers_to_requirement():
    """Save a supplier and attach it directly to a new requirement."""
    uid = str(uuid.uuid4())[:8]
    _, headers = _register_and_token(uid)

    # Requirement 1: discover and save a supplier
    req1_id = _create_requirement(headers, uid)
    matches = _discover_suppliers(headers, req1_id)
    supplier_id = matches[0]["supplier"]["id"]

    client.post(
        "/api/v1/saved-suppliers/",
        json={"supplier_id": supplier_id, "category": "Test Cat", "status": "preferred"},
        headers=headers,
    )

    # Requirement 2: attach saved supplier
    req2_id = _create_requirement(headers, uid + "_B")
    attach_res = client.post(
        f"/api/v1/saved-suppliers/attach-to-requirement/{req2_id}",
        json={"supplier_ids": [supplier_id]},
        headers=headers,
    )
    assert attach_res.status_code == 200
    data = attach_res.json()
    assert data["message"].startswith("Successfully attached")


# ────────────────────────────────────────────────────────────────────────────
# 3. Price Trend Analytics
# ────────────────────────────────────────────────────────────────────────────

def test_price_trends_endpoint():
    """Price-trends endpoint should return the expected schema."""
    uid = str(uuid.uuid4())[:8]
    _, headers = _register_and_token(uid)

    res = client.get("/api/v1/analytics/price-trends", headers=headers)
    assert res.status_code == 200, f"Price-trends failed: {res.text}"

    data = res.json()
    assert "total_quotations_analyzed" in data
    assert "category_summary" in data
    assert "supplier_performance" in data
    assert "time_series" in data
    assert isinstance(data["category_summary"], list)
    assert isinstance(data["supplier_performance"], list)


# ────────────────────────────────────────────────────────────────────────────
# 4. Market Intelligence Agent
# ────────────────────────────────────────────────────────────────────────────

def test_market_intelligence_agent():
    """Market Intelligence Agent should return structured insights for a requirement."""
    uid = str(uuid.uuid4())[:8]
    _, headers = _register_and_token(uid)
    req_id = _create_requirement(headers, uid)

    res = client.get(f"/api/v1/analytics/market-intelligence/{req_id}", headers=headers)
    assert res.status_code == 200, f"Market intelligence failed: {res.text}"

    data = res.json()
    assert "market_sentiment" in data
    assert "analysis_summary" in data
    assert "supply_chain_risks" in data
    assert "key_opportunities" in data
    assert "recommended_actions" in data
    assert "recommended_purchase_timing" in data

    # Verify types
    assert isinstance(data["supply_chain_risks"], list)
    assert isinstance(data["key_opportunities"], list)
    assert isinstance(data["recommended_actions"], list)
    assert data["market_sentiment"] in ("bullish", "bearish", "stable", "volatile")


# ────────────────────────────────────────────────────────────────────────────
# 5. Supplier Risk Analysis (multi-dimensional via supplier intelligence)
# ────────────────────────────────────────────────────────────────────────────

def test_supplier_risk_analysis_in_discovery():
    """
    Verify that discovered supplier matches include multi-dimensional
    risk analysis fields within rank_explanation.
    """
    uid = str(uuid.uuid4())[:8]
    _, headers = _register_and_token(uid)
    req_id = _create_requirement(headers, uid)
    matches = _discover_suppliers(headers, req_id)

    explanation = matches[0].get("rank_explanation", {})

    # Phase 3 risk fields should be present
    assert "trust_score" in explanation, "trust_score missing from rank_explanation"
    assert "summary" in explanation, "summary missing from rank_explanation"


# ────────────────────────────────────────────────────────────────────────────
# 6. Multi-Approver RFQ Workflow
# ────────────────────────────────────────────────────────────────────────────

def test_multi_approver_workflow_full_approval():
    """
    Full happy path: submit for approval → approve step 1 → approve step 2
    → verify RFQ status becomes 'approved'.
    """
    uid = str(uuid.uuid4())[:8]
    _, headers = _register_and_token(uid)
    req_id = _create_requirement(headers, uid)
    _discover_suppliers(headers, req_id)
    rfq_id = _generate_rfq(headers, req_id)

    # 1. Submit for approval
    submit_res = client.post(f"/api/v1/rfq/{rfq_id}/submit-for-approval", headers=headers)
    assert submit_res.status_code == 200, f"Submit-for-approval failed: {submit_res.text}"
    steps = submit_res.json()
    assert len(steps) == 2
    assert steps[0]["step_number"] == 1
    assert steps[1]["step_number"] == 2
    assert all(s["status"] == "pending" for s in steps)

    # Verify RFQ status is now pending_approval
    rfq_res = client.get(f"/api/v1/rfq/{rfq_id}", headers=headers)
    assert rfq_res.json()["status"] == "pending_approval"

    # 2. Approve Step 1 (Technical Review)
    step1_res = client.post(
        f"/api/v1/rfq/{rfq_id}/approve-step",
        json={"step_number": 1, "comments": "Specs look good, supplier shortlist approved."},
        headers=headers,
    )
    assert step1_res.status_code == 200, f"Approve step 1 failed: {step1_res.text}"
    # RFQ still pending after step 1 only
    assert step1_res.json()["status"] == "pending_approval"

    # 3. Approve Step 2 (Director Approval)
    step2_res = client.post(
        f"/api/v1/rfq/{rfq_id}/approve-step",
        json={"step_number": 2, "comments": "Director sign-off granted."},
        headers=headers,
    )
    assert step2_res.status_code == 200, f"Approve step 2 failed: {step2_res.text}"
    assert step2_res.json()["status"] == "approved", (
        f"Expected 'approved' after all steps, got '{step2_res.json()['status']}'"
    )


def test_multi_approver_workflow_rejection():
    """
    Rejection path: submit for approval → reject step 1
    → verify RFQ reverts to 'draft'.
    """
    uid = str(uuid.uuid4())[:8]
    _, headers = _register_and_token(uid)
    req_id = _create_requirement(headers, uid)
    _discover_suppliers(headers, req_id)
    rfq_id = _generate_rfq(headers, req_id)

    # Submit for approval
    submit_res = client.post(f"/api/v1/rfq/{rfq_id}/submit-for-approval", headers=headers)
    assert submit_res.status_code == 200

    # Reject step 1
    reject_res = client.post(
        f"/api/v1/rfq/{rfq_id}/reject-step",
        json={"step_number": 1, "comments": "Supplier list requires revision — missing REACH certifications."},
        headers=headers,
    )
    assert reject_res.status_code == 200, f"Reject step failed: {reject_res.text}"
    assert reject_res.json()["status"] == "draft", (
        f"Expected RFQ reverted to 'draft', got '{reject_res.json()['status']}'"
    )


def test_multi_approver_resubmit_after_rejection():
    """Verify a rejected RFQ can be re-submitted for approval."""
    uid = str(uuid.uuid4())[:8]
    _, headers = _register_and_token(uid)
    req_id = _create_requirement(headers, uid)
    _discover_suppliers(headers, req_id)
    rfq_id = _generate_rfq(headers, req_id)

    # Submit → reject
    client.post(f"/api/v1/rfq/{rfq_id}/submit-for-approval", headers=headers)
    client.post(
        f"/api/v1/rfq/{rfq_id}/reject-step",
        json={"step_number": 1, "comments": "Needs revision."},
        headers=headers,
    )

    # Re-submit after correction
    resubmit_res = client.post(f"/api/v1/rfq/{rfq_id}/submit-for-approval", headers=headers)
    assert resubmit_res.status_code == 200
    steps = resubmit_res.json()
    assert all(s["status"] == "pending" for s in steps), "Re-submitted steps should all be pending"


def test_approve_already_approved_step_returns_400():
    """Approving an already-approved step should return 400."""
    uid = str(uuid.uuid4())[:8]
    _, headers = _register_and_token(uid)
    req_id = _create_requirement(headers, uid)
    _discover_suppliers(headers, req_id)
    rfq_id = _generate_rfq(headers, req_id)

    client.post(f"/api/v1/rfq/{rfq_id}/submit-for-approval", headers=headers)
    client.post(f"/api/v1/rfq/{rfq_id}/approve-step", json={"step_number": 1}, headers=headers)

    # Attempt to approve again
    double_res = client.post(f"/api/v1/rfq/{rfq_id}/approve-step", json={"step_number": 1}, headers=headers)
    assert double_res.status_code == 400
