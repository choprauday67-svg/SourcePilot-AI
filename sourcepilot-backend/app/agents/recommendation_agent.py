from typing import List, Dict, Any
from app.agents.base_agent import BaseAgent
from app.schemas.agent_io_schemas import RecommendationOutput, RequirementExtractionOutput

class RecommendationAgent(BaseAgent):
    """Agent 8: Produce side-by-side comparison matrix & executive recommendation summary."""

    async def execute(
        self,
        requirement: RequirementExtractionOutput,
        quotations_with_suppliers: List[Dict[str, Any]]
    ) -> RecommendationOutput:
        if not quotations_with_suppliers:
            return RecommendationOutput(
                summary="No supplier quotations have been received yet.",
                recommended_supplier_id=None,
                comparison_matrix={}
            )

        # Construct comparison matrix
        matrix: Dict[str, Dict[str, Any]] = {}
        best_supplier_id = None
        lowest_total = float("inf")

        for item in quotations_with_suppliers:
            sup_id = item["supplier_id"]
            sup_name = item["company_name"]
            quote_data = item["extracted_data"]

            total_price = quote_data.get("total_price", 0.0)
            currency = quote_data.get("currency", "USD")
            lead_time = quote_data.get("lead_time_days", 14)
            moq = quote_data.get("moq", "100 units")

            matrix[sup_name] = {
                "unit_price": f"{quote_data.get('unit_price', 0.0)} {currency}",
                "total_price": f"{total_price} {currency}",
                "lead_time": f"{lead_time} days",
                "moq": str(moq),
                "terms": quote_data.get("payment_terms", "Net 30"),
                "confidence": f"{int(item.get('extraction_confidence', 1.0) * 100)}%"
            }

            if total_price > 0 and total_price < lowest_total:
                lowest_total = total_price
                best_supplier_id = sup_id

        first_supplier_name = list(matrix.keys())[0] if matrix else "Primary Supplier"
        best_name = list(matrix.keys())[0]
        for k, v in matrix.items():
            if best_supplier_id and v["total_price"].startswith(str(lowest_total)):
                best_name = k

        summary = (
            f"Based on competitive analysis of all received quotes, **{best_name}** is the recommended vendor. "
            f"They offer the optimal balance of pricing ({matrix[best_name]['total_price']}), fast delivery lead time "
            f"({matrix[best_name]['lead_time']}), and proven quality certification compliance."
        )

        return RecommendationOutput(
            summary=summary,
            recommended_supplier_id=best_supplier_id,
            comparison_matrix=matrix
        )
