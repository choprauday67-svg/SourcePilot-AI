from app.agents.base_agent import BaseAgent
from app.infrastructure.email.base import EmailProvider, EmailMessage, EmailSendResult
from app.infrastructure.email.mailtrap_provider import MailtrapProvider

class EmailAutomationAgent(BaseAgent):
    """Agent 6: Personalize and dispatch approved RFQs to selected suppliers."""

    def __init__(self, email_provider: EmailProvider = None):
        super().__init__()
        self.email_provider = email_provider or MailtrapProvider()

    async def execute(
        self,
        supplier_name: str,
        supplier_email: str,
        rfq_title: str,
        rfq_markdown: str
    ) -> EmailSendResult:
        subject = f"[RFQ] {rfq_title}"
        body = f"""Dear Sales Team at {supplier_name},

We are reaching out via SourcePilot AI Procurement to invite you to submit a quotation for the following requirement:

{rfq_markdown}

Please reply directly to this email with your formal quotation details.

Best regards,  
Procurement Team  
SourcePilot AI System
"""
        message = EmailMessage(
            to_email=supplier_email,
            to_name=supplier_name,
            subject=subject,
            body_markdown=body
        )
        return await self.email_provider.send_email(message)
