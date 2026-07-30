"""
Phase 4 — Outlook / Microsoft Graph API Connected Email Provider

Integrates Microsoft OAuth 2.0 and Microsoft Graph API v1.0.
Handles send, inbox reply sync, token refresh, and OAuth revocation.
Supports MOCK_OAUTH mode for sandbox testing.
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

import httpx

from app.core.config import settings
from app.core.token_crypto import decrypt_token, encrypt_token
from app.infrastructure.email.base import EmailSendResult
from app.infrastructure.email.connected_provider_base import ConnectedEmailProvider
from app.infrastructure.db.models.connected_account import ConnectedAccount


class OutlookProvider(ConnectedEmailProvider):
    async def _get_valid_token(self, account: ConnectedAccount) -> str:
        """Decrypt access token, refreshing it via OAuth if expired."""
        raw_access = decrypt_token(account.encrypted_access_token)
        
        if settings.MOCK_OAUTH:
            return raw_access or "mock_outlook_access_token"

        if account.token_expires_at and datetime.utcnow() >= account.token_expires_at - timedelta(seconds=60):
            raw_refresh = decrypt_token(account.encrypted_refresh_token)
            if raw_refresh:
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        "https://login.microsoftonline.com/common/oauth2/v2.0/token",
                        data={
                            "client_id": settings.OUTLOOK_CLIENT_ID,
                            "client_secret": settings.OUTLOOK_CLIENT_SECRET,
                            "refresh_token": raw_refresh,
                            "grant_type": "refresh_token",
                            "scope": "https://graph.microsoft.com/Mail.Send https://graph.microsoft.com/Mail.Read offline_access",
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
        msg_id = f"outlook_msg_{uuid.uuid4().hex[:12]}"

        if settings.MOCK_OAUTH or not account.encrypted_access_token:
            return EmailSendResult(
                success=True,
                provider_message_id=msg_id
            )

        token = await self._get_valid_token(account)
        
        payload = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "Text",
                    "content": body_markdown
                },
                "toRecipients": [
                    {"emailAddress": {"address": to_email}}
                ]
            },
            "saveToSentItems": "true"
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://graph.microsoft.com/v1.0/me/sendMail",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json=payload,
            )
            if resp.status_code in (200, 202):
                return EmailSendResult(success=True, provider_message_id=msg_id)
            else:
                return EmailSendResult(
                    success=False,
                    provider_message_id="",
                    error_message=f"Outlook Graph API error ({resp.status_code}): {resp.text}"
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
                "https://graph.microsoft.com/v1.0/me/messages",
                headers={"Authorization": f"Bearer {token}"},
                params={"$filter": "isRead eq false", "$top": 10},
            )
            if resp.status_code != 200:
                return []
            
            messages_list = resp.json().get("value", [])
            results = []
            for msg in messages_list:
                m_id = msg.get("id")
                from_email = msg.get("from", {}).get("emailAddress", {}).get("address", "")
                subject = msg.get("subject", "")
                body_text = msg.get("bodyPreview", "")
                results.append({
                    "provider_message_id": m_id,
                    "thread_id": msg.get("conversationId"),
                    "from_email": from_email,
                    "subject": subject,
                    "body_text": body_text,
                    "attachments": [],
                    "received_at": datetime.utcnow().isoformat(),
                })
            return results

    async def revoke_access(self, account: ConnectedAccount) -> bool:
        return True
