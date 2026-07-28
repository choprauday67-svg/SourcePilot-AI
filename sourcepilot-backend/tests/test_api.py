import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"

def test_register_and_login_flow():
    # 1. Register new organization
    reg_payload = {
        "org_name": "Test Acme Sourcing",
        "email": "buyer@acmesourcing.com",
        "password": "SecretPassword123!",
        "full_name": "Jane Doe"
    }
    res_reg = client.post("/api/v1/auth/register", json=reg_payload)
    assert res_reg.status_code == 200
    data = res_reg.json()
    assert "access_token" in data
    token = data["access_token"]

    # 2. Login with registered user
    login_payload = {
        "email": "buyer@acmesourcing.com",
        "password": "SecretPassword123!"
    }
    res_login = client.post("/api/v1/auth/login", json=login_payload)
    assert res_login.status_code == 200
    assert "access_token" in res_login.json()

    # 3. Fetch requirement with JWT
    headers = {"Authorization": f"Bearer {token}"}
    req_payload = {
        "raw_text": "Need 500 units of industrial-grade brushless DC motors, ISO 9001 certified, delivered to Austin, TX within 3 weeks, budget $15,000."
    }
    res_req = client.post("/api/v1/requirements", json=req_payload, headers=headers)
    assert res_req.status_code == 200
    req_data = res_req.json()
    assert req_data["status"] == "draft"
    req_id = req_data["id"]

    # 4. Discover & Rank Suppliers
    res_disc = client.post(f"/api/v1/requirements/{req_id}/suppliers/discover", headers=headers)
    assert res_disc.status_code == 200
    ranked = res_disc.json()
    assert len(ranked) > 0
    assert "rank_explanation" in ranked[0]

    # 5. Generate RFQ
    res_rfq = client.post(f"/api/v1/rfq/generate/{req_id}", headers=headers)
    assert res_rfq.status_code == 200
    rfq_data = res_rfq.json()
    assert rfq_data["status"] == "draft"
    rfq_id = rfq_data["id"]

    # 6. Approve RFQ
    res_app = client.post(f"/api/v1/rfq/{rfq_id}/approve", headers=headers)
    assert res_app.status_code == 200
    assert res_app.json()["status"] == "approved"

    # 7. Dispatch RFQ
    res_send = client.post(f"/api/v1/rfq/{rfq_id}/send", headers=headers)
    assert res_send.status_code == 200

    # 8. Submit Manual Quote & Get Recommendation
    sup_id = ranked[0]["supplier"]["id"]
    quote_payload = {
        "requirement_id": req_id,
        "supplier_id": sup_id,
        "unit_price": 24.50,
        "total_price": 12250.0,
        "currency": "USD",
        "moq": "100 units",
        "lead_time_days": 14,
        "warranty": "1 Year",
        "payment_terms": "Net 30"
    }
    res_quote = client.post("/api/v1/quotations/manual", json=quote_payload, headers=headers)
    assert res_quote.status_code == 200

    res_rec = client.get(f"/api/v1/quotations/recommendation/{req_id}", headers=headers)
    assert res_rec.status_code == 200
    assert "summary" in res_rec.json()
