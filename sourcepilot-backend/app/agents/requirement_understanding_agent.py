from app.agents.base_agent import BaseAgent
from app.schemas.agent_io_schemas import RequirementExtractionOutput

class RequirementUnderstandingAgent(BaseAgent):
    """Agent 1: Convert natural language procurement requirement into structured schema."""

    async def execute(self, raw_text: str) -> RequirementExtractionOutput:
        system_instruction = (
            "You are an expert enterprise Procurement Analyst. Analyze the natural language "
            "procurement requirement and extract structured attributes precisely according to the requested JSON schema. "
            "Never hallucinate unmentioned strict requirements, but infer standard units or category if obvious."
        )
        prompt = f"Procurement Request: \"{raw_text}\""
        return await self.ai_provider.generate_structured(prompt, RequirementExtractionOutput, system_instruction)
