from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Options: "cloud" or "local"
    AI_STACK_MODE: str = "cloud"
    
    # Cloud Keys
    GROQ_API_KEY: str | None = None
    
    # Local Model Paths
    MODEL_PATH_LOGIC: str = "./models/function-gemma-it.gguf"
    MODEL_PATH_NARRATIVE: str = "./models/llama-3-8b.gguf"

    class Config:
        env_file = ".env"

settings = Settings()