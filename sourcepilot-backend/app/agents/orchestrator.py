from app.agents.requirement_understanding_agent import RequirementUnderstandingAgent
from app.agents.supplier_discovery_agent import SupplierDiscoveryAgent
from app.agents.supplier_intelligence_agent import SupplierIntelligenceAgent
from app.agents.supplier_ranking_agent import SupplierRankingAgent
from app.agents.rfq_generator_agent import RFQGeneratorAgent
from app.agents.email_automation_agent import EmailAutomationAgent
from app.agents.quotation_extraction_agent import QuotationExtractionAgent
from app.agents.recommendation_agent import RecommendationAgent
from app.agents.market_intelligence_agent import MarketIntelligenceAgent  # Phase 3


class AgentOrchestrator:
    """Master Pipeline Orchestrator coordinating all 9 specialized AI agents."""

    def __init__(self):
        self.requirement_understanding_agent = RequirementUnderstandingAgent()
        self.supplier_discovery_agent = SupplierDiscoveryAgent()
        self.supplier_intelligence_agent = SupplierIntelligenceAgent()
        self.supplier_ranking_agent = SupplierRankingAgent()
        self.rfq_generator_agent = RFQGeneratorAgent()
        self.email_automation_agent = EmailAutomationAgent()
        self.quotation_extraction_agent = QuotationExtractionAgent()
        self.recommendation_agent = RecommendationAgent()
        self.market_intelligence_agent = MarketIntelligenceAgent()  # Phase 3


orchestrator = AgentOrchestrator()
