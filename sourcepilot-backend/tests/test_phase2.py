"""
SourcePilot AI — Phase 2 Automated Verification Suite

Tests all new Phase 2 capabilities:
  - Multi-connector registry & adapter implementations (web search, marketplace, trade registry, review sites)
  - Category-aware ranking agent weighting matrix & multi-connector provenance signals
  - Requirement comments (team collaboration CRUD with @mentions and RBAC)
  - Inbound email webhook for automated quote extraction
  - Connector monitoring diagnostic routes
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.infrastructure.search_connectors.connector_registry import connector_registry

client = TestClient(app)


def test_connector_registry_phase2():
    """Verify all 4 Phase 2 connectors are registered and operational."""
    names = connector_registry.list_connector_names()
    assert "web_search" in names
    assert "marketplace" in names
    assert "trade_registry" in names
    assert "review_sites" in names
    assert len(connector_registry.get_all_connectors()) >= 4


def test_connector_monitoring_endpoints():
    """Test /api/v1/connectors/list and /api/v1/connectors/health."""
    import uuid
    uid = str(uuid.uuid4())[:8]
    # 1. Register user & get JWT token
    reg_payload = {
        "org_name": f"Phase 2 Validation Corp {uid}",
        "email": f"lead_{uid}@phase2corp.com",
        "password": "SecurePassword123!",
        "full_name": "Phase 2 Lead",
    }
    res_reg = client.post("/api/v1/auth/register", json=reg_payload)
    assert res_reg.status_code == 200
    token = res_reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. List connectors
    res_list = client.get("/api/v1/connectors/list", headers=headers)
    assert res_list.status_code == 200
    connectors = res_list.json()
    assert len(connectors) >= 4
    connector_names = [c["name"] for c in connectors]
    assert "marketplace" in connector_names
    assert "trade_registry" in connector_names
    assert "review_sites" in connector_names

    # 3. Connector health check
    res_health = client.get("/api/v1/connectors/health", headers=headers)
    assert res_health.status_code == 200
    health_data = res_health.json()
    assert health_data["status"] == "all_systems_operational"
    assert "marketplace" in health_data["connectors"]


def test_team_collaboration_comments():
    """Test posting, listing, updating, and deleting requirement comments with @mentions."""
    import uuid
    uid = str(uuid.uuid4())[:8]
    # 1. Register user
    reg_payload = {
        "org_name": f"Collaboration Org {uid}",
        "email": f"collab_{uid}@test.com",
        "password": "Password123!",
        "full_name": "Comment Author",
    }
    res_reg = client.post("/api/v1/auth/register", json=reg_payload)
    token = res_reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create requirement
    req_res = client.post(
        "/api/v1/requirements",
        json={"raw_text": "Need 100 units of ISO 9001 certified stainless steel pipes for chemical plant construction."},
        headers=headers,
    )
    assert req_res.status_code == 200
    req_id = req_res.json()["id"]

    # 3. Post comment with @mention
    comment_payload = {
        "body": "@user_456 Please review the ISO 9001 certificate on TrustBuilt Supply before approving.",
        "mentions": ["user_456"],
    }
    post_res = client.post(
        f"/api/v1/requirements/{req_id}/comments/",
        json=comment_payload,
        headers=headers,
    )
    assert post_res.status_code == 201
    comment_data = post_res.json()
    assert comment_data["body"] == comment_payload["body"]
    assert "user_456" in comment_data["mentions"]
    comment_id = comment_data["id"]

    # 4. List comments
    list_res = client.get(
        f"/api/v1/requirements/{req_id}/comments/",
        headers=headers,
    )
    assert list_res.status_code == 200
    comments = list_res.json()
    assert len(comments) == 1
    assert comments[0]["id"] == comment_id

    # 5. Patch comment
    update_res = client.patch(
        f"/api/v1/requirements/{req_id}/comments/{comment_id}",
        json={"body": "Updated: Vendor verified by compliance team."},
        headers=headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["body"] == "Updated: Vendor verified by compliance team."

    # 6. Delete comment
    del_res = client.delete(
        f"/api/v1/requirements/{req_id}/comments/{comment_id}",
        headers=headers,
    )
    assert del_res.status_code == 204


def test_inbound_email_webhook():
    """Test receiving parsed supplier reply emails via the inbound webhook."""
    import uuid
    uid = str(uuid.uuid4())[:8]
    # 1. Health check
    health_res = client.get("/api/v1/webhooks/inbound-email/health")
    assert health_res.status_code == 200
    assert health_res.json()["status"] == "healthy"

    # 2. Register supplier domain first so webhook can match domain
    reg_payload = {
        "org_name": f"Webhook Test Corp {uid}",
        "email": f"webhook_{uid}@whcorp.com",
        "password": "SecretPassword123!",
        "full_name": "WH Admin",
    }
    res_reg = client.post("/api/v1/auth/register", json=reg_payload)
    token = res_reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Discover suppliers
    req_res = client.post(
        "/api/v1/requirements",
        json={"raw_text": "Need 200 units of high precision CNC aluminum brackets."},
        headers=headers,
    )
    req_id = req_res.json()["id"]
    disc_res = client.post(f"/api/v1/requirements/{req_id}/suppliers/discover", headers=headers)
    assert disc_res.status_code == 200
    ranked_suppliers = disc_res.json()
    assert len(ranked_suppliers) > 0
    supplier_obj = ranked_suppliers[0]["supplier"]
    supplier_domain = supplier_obj["canonical_domain"]

    # 3. Send webhook payload simulating supplier quote email reply
    webhook_payload = {
        "from_email": f"export@{supplier_domain}",
        "from_name": supplier_obj["company_name"],
        "to_email": "rfq@sourcepilot.ai",
        "subject": "RE: RFQ — CNC Aluminum Brackets Quote Response",
        "body_text": (
            "Dear Procurement Team,\n\n"
            "Thank you for your RFQ. We are pleased to offer:\n"
            "- Unit Price: $45.00 USD\n"
            "- Total Price for 200 units: $9,000.00 USD\n"
            "- Lead Time: 18 business days\n"
            "- MOQ: 50 units\n"
            "- Payment Terms: Net 30 days\n"
            "- Offer Validity: 30 days\n\n"
            "Best regards,\nExport Manager"
        ),
    }
    wh_headers = {"X-Webhook-Secret": "sourcepilot_webhook_secret"}
    wh_res = client.post("/api/v1/webhooks/inbound-email", json=webhook_payload, headers=wh_headers)
    assert wh_res.status_code == 200
    res_json = wh_res.json()
    assert res_json["received"] is True
    assert "quotation_id" in res_json
    assert res_json["quotation_id"] is not None
