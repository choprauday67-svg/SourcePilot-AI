"""
Phase 4 — EmailAutomationAgent

Generates personalized, structured email draft proposals for suppliers.
CRITICAL SAFEGUARD: AI NEVER autonomously sends external emails.
Generates draft subject and body text for human review and explicit send action.
"""
from typing import Dict, Any, Optional
from app.agents.base_agent import BaseAgent


class EmailAutomationAgent(BaseAgent):
    """Agent 6: Personalize RFQ email drafts and follow-up reminders for human review."""

    async def execute(
        self,
        supplier_name: str,
        supplier_email: str,
        rfq_title: str,
        rfq_markdown: str,
        is_follow_up: bool = False,
    ) -> Dict[str, str]:
        """
        Generate email draft proposal (subject & body) for human approval.
        Returns dict with {"subject": ..., "body_markdown": ...}.
        """
        if is_follow_up:
            subject = f"[Follow-Up] Quotation Request: {rfq_title}"
            body = (
                f"Dear Sales Team at {supplier_name},\n\n"
                f"We are following up regarding our earlier quotation request for: **{rfq_title}**.\n\n"
                "We would appreciate it if you could confirm your availability and submit your formal quotation details "
                "at your earliest convenience.\n\n"
                "Summary of requirement:\n"
                f"{rfq_markdown}\n\n"
                "Please reply directly to this email with your quote.\n\n"
                "Best regards,\n"
                "Procurement Team\n"
                "SourcePilot AI Platform"
            )
        else:
            subject = f"[RFQ] Invitation to Quote: {rfq_title}"
            body = (
                f"Dear Sales Team at {supplier_name},\n\n"
                "We are reaching out via SourcePilot AI Procurement to invite your organization to submit a formal quotation "
                f"for the following requirement:\n\n"
                f"{rfq_markdown}\n\n"
                "Please reply directly to this email with your unit price, total lead time, payment terms, and warranty details.\n\n"
                "Best regards,\n"
                "Procurement Team\n"
                "SourcePilot AI Platform"
            )

        return {
            "subject": subject,
            "body_markdown": body,
            "recipient_email": supplier_email,
            "recipient_name": supplier_name,
        }
