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
    LLM_PROVIDER: str = "google"  # ollama|openai|google
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = ""
    OPENAI_GEN_MODEL: str = "gpt-4o-mini"
    OPENAI_CLASSIFY_MODEL: str = "gpt-4o-mini"
    GOOGLE_API_KEY: str = ""
    GOOGLE_GEN_MODEL: str = "gemini-3.1-pro-preview"
    GOOGLE_CLASSIFY_MODEL: str = "gemini-1.5-flash"
    
    # agent configuration
    AGENT_TEMPERATURE: float = 0.7
    AGENT_MAX_ITERATIONS: int = 10
    LLM_TIMEOUT_SECONDS: float = 12.0

    # game runtime configuration
    GAME_MODE: str = "llm"  # programmatic|hybrid|llm
    ENABLE_LLM_NARRATION: bool = False
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://localhost:4173"
    CORS_ALLOW_ORIGIN_REGEX: str = r"^https?://(localhost|127\.0\.0\.1|0\.0\.0\.0)(:\d+)?$"
    HISTORY_RECENT_TURNS: int = 8
    HISTORY_SUMMARY_MAX_CHARS: int = 700

    class Config:
        env_file = ".env"

settings = Settings()