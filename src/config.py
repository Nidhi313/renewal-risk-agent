"""Centralized settings, loaded from environment variables (or .env locally)."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    google_api_key: str = ""
    groq_api_key: str = ""

    # Primary provider for the agent, and the one tried if it fails (rate limit,
    # retired model, outage). Set FALLBACK_PROVIDER="" to disable fallback.
    model_provider: str = "groq"  # "groq" | "gemini" | "ollama"
    fallback_provider: str = "gemini"

    # Model IDs live in config, not code, so a provider retiring a model is a
    # redeploy with a new env var rather than a code change.
    groq_model: str = "openai/gpt-oss-120b"
    gemini_model: str = "gemini-3.6-flash"
    ollama_model: str = "llama3.2"

    # Assessments are cached per customer per day. The data is synthetic and
    # fixed, so re-running the same customer burns free-tier quota for nothing.
    cache_ttl_seconds: int = 6 * 60 * 60

    enable_tracing: bool = False
    phoenix_collector_endpoint: str = "http://localhost:6006"
    judge_sample_rate: float = 0.08


settings = Settings()
