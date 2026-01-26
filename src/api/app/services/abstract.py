from abc import ABC, abstractmethod
from typing import Optional

class LLMProvider(ABC):
    @abstractmethod
    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generates narrative text."""
        pass

    @abstractmethod
    async def classify_intent(self, user_input: str) -> dict:
        """Returns structured JSON logic."""
        pass