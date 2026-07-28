from app.agents.base_agent import BaseAgent
from app.schemas.agent_io_schemas import QuotationExtractionOutput

class QuotationExtractionAgent(BaseAgent):
    """Agent 7: Parse incoming email replies or unstructured quote text into structured JSON."""

    async def execute(self, email_body: str) -> QuotationExtractionOutput:
        system_instruction = (
            "You are a meticulous procurement quote parsing AI. Extract financial unit price, "
            "total price, currency, MOQ, lead time days, payment terms, and validity period from the supplier's quotation response text."
        )
        prompt = f"Supplier Quotation Email:\n\"\"\"{email_body}\"\"\""
        return await self.ai_provider.generate_structured(prompt, QuotationExtractionOutput, system_instruction)
