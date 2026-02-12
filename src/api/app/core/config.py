from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # server configuration
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    
    # ollama configuration
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_GEN_MODEL: str = "qwen3:8b"
    OLLAMA_CLASSIFY_MODEL: str = "qwen3:8b" # pre tool calling update, use the same model for both gen and classify
    
    # agent configuration
    AGENT_TEMPERATURE: float = 0.7
    AGENT_MAX_ITERATIONS: int = 10

    class Config:
        env_file = ".env"

settings = Settings()