"""Centralized settings, loaded from environment variables."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    google_api_key: str = ""
    groq_api_key: str = ""
    model_provider: str = "gemini"   # "gemini" or "ollama" or "groq" -- set in .env
    phoenix_collector_endpoint: str = "http://localhost:6006"
    judge_sample_rate: float = 0.08

    class Config:
        env_file = ".env"

settings = Settings()
