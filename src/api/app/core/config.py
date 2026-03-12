from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # server configuration
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    
    # ollama configuration
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_GEN_MODEL: str = "qwen3:8b"
    OLLAMA_CLASSIFY_MODEL: str = "qwen3:8b" # pre tool calling update, use the same model for both gen and classify

    # llm provider configuration
    LLM_PROVIDER: str = "ollama"  # ollama|openai|google
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = ""
    OPENAI_GEN_MODEL: str = "gpt-4o-mini"
    OPENAI_CLASSIFY_MODEL: str = "gpt-4o-mini"
    GOOGLE_API_KEY: str = "AIzaSyA74HajsvWgPXeROsnmRApYDcuxrFwe1bg"
    GOOGLE_GEN_MODEL: str = "gemini-2.0-flash"
    GOOGLE_CLASSIFY_MODEL: str = "gemini-2.0-flash"
    
    # agent configuration
    AGENT_TEMPERATURE: float = 0.7
    AGENT_MAX_ITERATIONS: int = 10

    # game runtime configuration
    GAME_MODE: str = "programmatic"  # programmatic|hybrid|llm
    ENABLE_LLM_NARRATION: bool = False

    class Config:
        env_file = ".env"

settings = Settings()