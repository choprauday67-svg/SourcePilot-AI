"""
Phase 4 — Gmail API Connected Email Provider

Integrates Google OAuth 2.0 and Gmail REST API v1.
Handles send, inbox reply sync, token refresh, and OAuth revocation.
Supports MOCK_OAUTH mode for sandbox testing.
"""
import uuid
import base64
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from email.mime.text import MIMEText

import httpx

from app.core.config import settings
from app.core.token_crypto import decrypt_token, encrypt_token
from app.infrastructure.email.base import EmailSendResult
from app.infrastructure.email.connected_provider_base import ConnectedEmailProvider
from app.infrastructure.db.models.connected_account import ConnectedAccount


class GmailProvider(ConnectedEmailProvider):
    async def _get_valid_token(self, account: ConnectedAccount) -> str:
        """Decrypt access token, refreshing it via OAuth if expired."""
        raw_access = decrypt_token(account.encrypted_access_token)
        
        if settings.MOCK_OAUTH:
            return raw_access or "mock_gmail_access_token"

        # Check if token is expired or about to expire in 60s
        if account.token_expires_at and datetime.utcnow() >= account.token_expires_at - timedelta(seconds=60):
            raw_refresh = decrypt_token(account.encrypted_refresh_token)
            if raw_refresh:
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        "https://oauth2.googleapis.com/token",
                        data={
                            "client_id": settings.GMAIL_CLIENT_ID,
                            "client_secret": settings.GMAIL_CLIENT_SECRET,
                            "refresh_token": raw_refresh,
                            "grant_type": "refresh_token",
                        },
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        new_access = data["access_token"]
                        expires_in = data.get("expires_in", 3600)
                        account.encrypted_access_token = encrypt_token(new_access)
                        account.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
                        account.status = "active"
                        return new_access
        return raw_access

    async def send_draft(
        self,
        account: ConnectedAccount,
        to_email: str,
        subject: str,
        body_markdown: str,
        reply_to_message_id: Optional[str] = None
    ) -> EmailSendResult:
        msg_id = f"gmail_msg_{uuid.uuid4().hex[:12]}"

        if settings.MOCK_OAUTH or not account.encrypted_access_token:
            return EmailSendResult(
                success=True,
                provider_message_id=msg_id
            )

        token = await self._get_valid_token(account)
        
        # Build MIME email message
        mime_msg = MIMEText(body_markdown, "plain")
        mime_msg["to"] = to_email
        mime_msg["from"] = account.email_address
        mime_msg["subject"] = subject
        if reply_to_message_id:
            mime_msg["In-Reply-To"] = reply_to_message_id
            mime_msg["References"] = reply_to_message_id

        raw_bytes = base64.urlsafe_b64encode(mime_msg.as_bytes()).decode("utf-8")

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json={"raw": raw_bytes},
            )
            if resp.status_code in (200, 201):
                res_data = resp.json()
                return EmailSendResult(success=True, provider_message_id=res_data.get("id", msg_id))
            else:
                return EmailSendResult(
                    success=False,
                    provider_message_id="",
                    error_message=f"Gmail API error ({resp.status_code}): {resp.text}"
                )

    async def sync_inbox_replies(
        self,
        account: ConnectedAccount,
        since_message_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        if settings.MOCK_OAUTH:
            return []

        token = await self._get_valid_token(account)
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://gmail.googleapis.com/gmail/v1/users/me/messages",
                headers={"Authorization": f"Bearer {token}"},
                params={"q": "is:unread label:INBOX"},
            )
            if resp.status_code != 200:
                return []
            
            messages_list = resp.json().get("messages", [])
            results = []
            for msg_meta in messages_list[:10]:
                m_id = msg_meta["id"]
                msg_resp = await client.get(
                    f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{m_id}",
                    headers={"Authorization": f"Bearer {token}"},
                )
                if msg_resp.status_code == 200:
                    m_data = msg_resp.json()
                    headers_dict = {h["name"].lower(): h["value"] for h in m_data.get("payload", {}).get("headers", [])}
                    from_email = headers_dict.get("from", "")
                    subject = headers_dict.get("subject", "")
                    body_text = m_data.get("snippet", "")
                    results.append({
                        "provider_message_id": m_id,
                        "thread_id": m_data.get("threadId"),
                        "from_email": from_email,
                        "subject": subject,
                        "body_text": body_text,
                        "attachments": [],
                        "received_at": datetime.utcnow().isoformat(),
                    })
            return results

    async def revoke_access(self, account: ConnectedAccount) -> bool:
        if settings.MOCK_OAUTH or not account.encrypted_access_token:
            return True

        token = decrypt_token(account.encrypted_access_token)
        if not token:
            return True

        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    "https://oauth2.googleapis.com/revoke",
                    params={"token": token},
                )
            return True
        except Exception:
            return True
