from abc import ABC, abstractmethod
from typing import Optional, Any

class LLMProvider(ABC):
    @abstractmethod
    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """generates narrative text."""
        pass

    @abstractmethod
    async def classify_intent(self, user_input: str) -> dict[str, Any]:
        """returns structured json logic."""
        pass