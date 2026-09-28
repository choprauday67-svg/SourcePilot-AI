import re
from typing import Dict, Any, Optional
from app.agents.base_agent import BaseAgent


def _clean_markdown_for_email(md_text: str) -> str:
    """Converts raw Markdown headings, bold markers, and rules into clean, elegant email body text."""
    if not md_text:
        return ""
    cleaned = md_text
    # Remove horizontal rules
    cleaned = re.sub(r'^\s*---\s*$', '', cleaned, flags=re.MULTILINE)
    # Convert ### section headings to clean uppercase labels
    cleaned = re.sub(r'^###\s*\d*\.?\s*(.+)$', r'\n\1:', cleaned, flags=re.MULTILINE)
    # Convert ## headings
    cleaned = re.sub(r'^##\s*(.+)$', r'\n\1:', cleaned, flags=re.MULTILINE)
    # Convert # headings
    cleaned = re.sub(r'^#\s*(.+)$', r'\1', cleaned, flags=re.MULTILINE)
    # Remove bold ** formatting
    cleaned = re.sub(r'\*\*(.+?)\*\*', r'\1', cleaned)
    # Clean up excess newline clutter
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    return cleaned.strip()


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
        # Clean title to remove requester name concatenation and duplicate RFQ prefixes
        clean_title = rfq_title
        # Remove requester name patterns (e.g. Uday Chopra, by Uday Chopra, - Uday Chopra)
        clean_title = re.sub(r'(?i)\s*(?:by|-|\(|\b)\s*Uday\s+Chopra.*$', '', clean_title)
        clean_title = re.sub(r'(?i)\s*(?:by|-|\(|\b)\s*[A-Z][a-z]+\s+[A-Z][a-z]+\b.*$', '', clean_title)
        # Strip redundant RFQ prefixes
        clean_title = clean_title.replace("Request for Quotation (RFQ) - ", "").replace("Request for Quotation (RFQ)-", "").replace("[RFQ] ", "").replace("[RFQ]", "").strip()

        display_title = clean_title if clean_title else "500.0x Industrial Brushless DC Motors"

        formatted_rfq_body = _clean_markdown_for_email(rfq_markdown)

        if is_follow_up:
            subject = f"[Follow-Up] Quotation Request: {display_title}"
            body = (
                f"Dear Sales Team at {supplier_name},\n\n"
                f"We are following up regarding our earlier quotation request for: {display_title}.\n\n"
                "We would appreciate it if you could confirm your availability and submit your formal quotation details "
                "at your earliest convenience.\n\n"
                "Summary of requirement:\n"
                f"{formatted_rfq_body}\n\n"
                "Please reply directly to this email with your quote.\n\n"
                "Best regards,\n"
                "Procurement Team\n"
                "SourcePilot AI Platform"
            )
        else:
            subject = f"[RFQ] Invitation to Quote: {display_title}"
            body = (
                f"Dear Sales Team at {supplier_name},\n\n"
                "We are reaching out via SourcePilot AI Procurement to invite your organization to submit a formal quotation "
                f"for the following requirement:\n\n"
                f"{formatted_rfq_body}\n\n"
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

