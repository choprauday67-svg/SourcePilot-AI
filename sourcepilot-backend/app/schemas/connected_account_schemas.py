"""
Phase 4 Connected Account Schemas
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class ConnectedAccountResponse(BaseModel):
    id: str
    user_id: str
    organization_id: str
    provider: str
    email_address: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class OAuthAuthorizeResponse(BaseModel):
    authorization_url: str
    provider: str
    state: str


class OAuthCallbackRequest(BaseModel):
    code: str
    state: str
    code_verifier: Optional[str] = None
