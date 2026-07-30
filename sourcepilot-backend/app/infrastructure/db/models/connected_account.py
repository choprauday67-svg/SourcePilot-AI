import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.infrastructure.db.base import Base

class ConnectedAccount(Base):
    """
    Phase 4 — User-Scoped Connected Mailbox (Gmail / Outlook OAuth 2.0).
    Stores encrypted tokens and connection metadata scoped strictly to user_id.
    """
    __tablename__ = "connected_accounts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    provider = Column(String, nullable=False)  # "gmail", "outlook", "smtp"
    email_address = Column(String, nullable=False)
    encrypted_access_token = Column(Text, nullable=True)
    encrypted_refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)
    status = Column(String, default="active")  # "active", "expired", "revoked"
    oauth_state = Column(String, nullable=True)  # CSRF validation state
    code_verifier = Column(String, nullable=True)  # PKCE code verifier
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", backref="connected_accounts")
    organization = relationship("Organization")
