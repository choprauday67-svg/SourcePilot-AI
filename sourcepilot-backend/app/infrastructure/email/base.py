from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

@dataclass
class EmailMessage:
    to_email: str
    subject: str
    body_markdown: str
    body_html: Optional[str] = None
    to_name: Optional[str] = None
    reply_to: Optional[str] = None
    metadata: Dict[str, Any] = None

@dataclass
class EmailSendResult:
    success: bool
    provider_message_id: str
    error_message: Optional[str] = None

class EmailProvider(ABC):
    @abstractmethod
    async def send_email(self, message: EmailMessage) -> EmailSendResult:
        """Send an email and return dispatch result."""
        pass
