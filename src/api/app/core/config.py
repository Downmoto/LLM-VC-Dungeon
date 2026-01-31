from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # server configuration
    PORT: int = 12000
    HOST: str = "0.0.0.0"
    
    class Config:
        env_file = ".env"

settings = Settings()