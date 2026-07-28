from abc import ABC, abstractmethod
from typing import Type, TypeVar, Optional, Dict, Any
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

class AIProvider(ABC):
    @abstractmethod
    async def generate_structured(self, prompt: str, schema: Type[T], system_instruction: Optional[str] = None) -> T:
        """Generate structured response matching Pydantic schema."""
        pass

    @abstractmethod
    async def generate_text(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        """Generate unstructured markdown/plain text response."""
        pass
