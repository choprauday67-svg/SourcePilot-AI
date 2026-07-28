from abc import ABC
from app.infrastructure.ai_providers.base import AIProvider
from app.infrastructure.ai_providers.gemini_provider import GeminiProvider

class BaseAgent(ABC):
    def __init__(self, ai_provider: AIProvider = None):
        self.ai_provider = ai_provider or GeminiProvider()
