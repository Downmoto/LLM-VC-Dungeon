from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # server configuration
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    
    # options: "cloud" or "local"
    AI_STACK_MODE: str = "local"
    
    # cloud keys
    GROQ_API_KEY: Optional[str] = None
    
    # local model paths
    MODEL_PATH_LOGIC: str = "./models/function-gemma-it.gguf"
    MODEL_PATH_NARRATIVE: str = "./models/llama-3-8b.gguf"

    class Config:
        env_file = ".env"

settings = Settings()