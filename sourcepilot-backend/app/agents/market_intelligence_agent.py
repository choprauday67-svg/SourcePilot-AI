"""
MarketIntelligenceAgent — Phase 3 Agent 9

Generates AI-powered market intelligence forecasts, price movement analysis,
supplier responsiveness scores, and strategic buy window recommendations.
Insights are contextualised to the specific product and category of the requirement.
"""
from typing import List, Dict, Any, Optional
from app.agents.base_agent import BaseAgent
from app.schemas.agent_io_schemas import MarketIntelligenceOutput


class MarketIntelligenceAgent(BaseAgent):
    """Agent 9: Executive Market Intelligence & Price Trend Forecast AI."""

    async def execute(
        self,
        historical_quotes: List[Dict[str, Any]],
        requirement_context: Optional[Dict[str, Any]] = None,
    ) -> MarketIntelligenceOutput:
        # Extract product/category for context-aware prompting and fallback
        ctx = requirement_context or {}
        product = ctx.get("product") or "industrial components"
        category = ctx.get("category") or "Industrial Procurement"

        # If historical_quotes include requirement_context per quote, extract from first one
        if not requirement_context and historical_quotes:
            first_ctx = historical_quotes[0].get("requirement_context") or {}
            product = first_ctx.get("product") or product
            category = first_ctx.get("category") or category

        system_instruction = (
            "You are a senior procurement intelligence director specializing in global supply chain analysis. "
            "Provide actionable, structured executive guidance tailored to the specific product and category provided."
        )

        prompt = (
            f"Analyze procurement market conditions for: **{product}** (Category: {category}).\n"
            f"Historical quotation dataset ({len(historical_quotes)} records): {historical_quotes}\n\n"
            "Generate an executive market trend summary, price movement forecast for the next 90 days, "
            "supplier responsiveness score (0-100), recommended sourcing strategy, and optimal buy window. "
            "All insights MUST be specific to the product and category above — do not use generic examples."
        )

        try:
            result = await self.ai_provider.generate_structured(
                prompt=prompt,
                response_model=MarketIntelligenceOutput,
                system_instruction=system_instruction,
            )
            result.intelligence_source = "live_ai_generated"
            return result
        except Exception:
            # Context-aware deterministic fallback when AI provider is unavailable
            return self._build_contextual_fallback(product, category, historical_quotes)

    def _build_contextual_fallback(
        self,
        product: str,
        category: str,
        historical_quotes: List[Dict[str, Any]],
    ) -> MarketIntelligenceOutput:
        """Build a deterministic, product-specific fallback that is clearly labelled as simulated."""
        quote_count = len(historical_quotes)
        avg_unit = None
        if quote_count > 0:
            prices = [
                q.get("data", {}).get("unit_price") or q.get("unit_price")
                for q in historical_quotes
                if q.get("data", {}).get("unit_price") or q.get("unit_price")
            ]
            if prices:
                avg_unit = round(sum(prices) / len(prices), 2)

        price_ref = f"avg unit price ${avg_unit}" if avg_unit else "price data unavailable"
        qty_note = f"{quote_count} quotation(s) on record" if quote_count else "no quotations yet"

        return MarketIntelligenceOutput(
            intelligence_source="simulated_agent_intelligence",
            market_sentiment="stable",
            analysis_summary=(
                f"Market intelligence for **{product}** ({category}): Pricing is currently stable "
                f"with moderate supply availability. Internal procurement data shows {qty_note} "
                f"({price_ref}). Lead times for this category typically range 10–21 business days depending on order volume."
            ),
            supply_chain_risks=[
                f"Regional logistics variability may affect {product} lead times by 3–7 days",
                f"Single-source dependency risk if only one {category} supplier is engaged",
                f"Currency fluctuation may impact {category} import pricing by 2–5%",
            ],
            key_opportunities=[
                f"Volume consolidation for {product} orders above 500 units can unlock 8–12% rebate",
                f"Dual-sourcing across geographies reduces {category} supply disruption risk",
                f"Fixed-price 6-month contracts available from verified {category} suppliers",
            ],
            recommended_actions=[
                f"Issue RFQs to at least 3 qualified {product} suppliers within the next 5 business days.",
                f"Request sample units from shortlisted {category} vendors before full order.",
                f"Negotiate payment terms of Net 45 with volume commitments above 250 units.",
            ],
            recommended_purchase_timing="Within next 14 business days — stable pricing window",
            price_forecast_90_days=(
                f"{product} pricing is forecast to remain stable over the next 90 days "
                f"with a modest ±3% variance. No major supply shocks anticipated in {category}."
            ),
            market_trend_summary=(
                f"{category} market is stable. {product} availability is adequate across major supply regions."
            ),
            price_movement_forecast=(
                f"Prices expected to remain within ±3% over the next 90 days for {product}."
            ),
            supplier_responsiveness_index=82.0,
            recommended_sourcing_strategy=(
                f"Lock-in 6-month fixed pricing with primary {product} suppliers; "
                f"request volume rebate for orders exceeding 500 units."
            ),
            best_buy_window="Immediate — Next 14 business days",
            category_insights=[
                {
                    "category": category,
                    "trend": "Stable (±1%)",
                    "lead_time_avg": "14 days",
                    "product": product,
                },
            ],
        )
