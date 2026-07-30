"""
Phase 4 Connected Email Provider Abstraction

Defines the abstract base interface for connected mailboxes (Gmail API, Outlook Graph API, and Mailtrap fallback).
Decouples business logic from specific API provider details.
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from app.infrastructure.email.base import EmailSendResult
from app.infrastructure.db.models.connected_account import ConnectedAccount


class ConnectedEmailProvider(ABC):
    @abstractmethod
    async def send_draft(
        self,
        account: ConnectedAccount,
        to_email: str,
        subject: str,
        body_markdown: str,
        reply_to_message_id: Optional[str] = None
    ) -> EmailSendResult:
        """Send an approved email draft through the connected mailbox."""
        pass

    @abstractmethod
    async def sync_inbox_replies(
        self,
        account: ConnectedAccount,
        since_message_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch inbound supplier email replies from the connected mailbox.
        Returns a list of raw email message dictionaries containing:
        - provider_message_id
        - thread_id
        - from_email
        - subject
        - body_text
        - attachments: list of {filename, content_type, size_bytes, content_bytes/base64}
        - received_at
        """
        pass

    @abstractmethod
    async def revoke_access(self, account: ConnectedAccount) -> bool:
        """Revoke OAuth tokens with the remote provider upon disconnect."""
        pass
