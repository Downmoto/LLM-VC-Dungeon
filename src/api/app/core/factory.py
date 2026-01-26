from app.core.config import settings
from app.services.groq_provider import GroqProvider
from app.services.local_provider import LocalProvider

def get_llm_provider():
    if settings.AI_STACK_MODE == "local":
        print("Loading LOCAL AI Stack (this may take a moment)...")
        return LocalProvider()
    else:
        print("Loading CLOUD AI Stack (Groq)...")
        return GroqProvider()
