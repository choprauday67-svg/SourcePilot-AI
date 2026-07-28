from app.agents.base_agent import BaseAgent
from app.schemas.agent_io_schemas import RequirementExtractionOutput, RFQGenerationOutput

class RFQGeneratorAgent(BaseAgent):
    """Agent 5: Generate professional RFQ document matching requirement specifications."""

    async def execute(
        self,
        requirement: RequirementExtractionOutput,
        org_name: str = "SourcePilot Enterprise Client"
    ) -> RFQGenerationOutput:
        title = f"Request for Quotation (RFQ) - {requirement.quantity}x {requirement.product}"
        
        specs_bullet = "\n".join([f"- {spec}" for spec in requirement.specifications]) or "- Standard manufacturer specifications"
        certs_bullet = "\n".join([f"- {cert}" for cert in requirement.must_have_certifications]) or "- Standard ISO compliance"

        markdown_content = f"""# Request for Quotation (RFQ)

**RFQ Title:** {title}  
**Issuing Organization:** {org_name}  
**Date:** 2026-07-28  

---

### 1. Procurement Summary & Scope
We are requesting binding quotes for the supply of **{requirement.quantity} {requirement.unit}** of **{requirement.product}**.

- **Category:** {requirement.category}
- **Required Delivery Location:** {requirement.delivery_location or "To be specified"}
- **Requested Delivery Timeline:** {requirement.timeline or "Within standard lead time"}

---

### 2. Technical Specifications
{specs_bullet}

---

### 3. Mandatory Compliance & Certifications
{certs_bullet}

---

### 4. Quote Submission Guidelines
Please respond with your formal quotation including:
1. Itemized unit price and total cost ({requirement.budget_range.currency if requirement.budget_range else 'USD'}).
2. Guaranteed lead time (days/weeks) to delivery location.
3. Minimum Order Quantity (MOQ) and tier discounts.
4. Payment terms (e.g., Net 30) and quote validity period.
"""

        return RFQGenerationOutput(
            title=title,
            sections={
                "scope": f"Supply of {requirement.quantity} {requirement.unit} of {requirement.product}",
                "specs": "\n".join(requirement.specifications),
                "guidelines": "Submit itemized quote with lead time & payment terms."
            },
            formatted_rfq_markdown=markdown_content
        )
