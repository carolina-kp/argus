from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Shared configuration, sourced from environment / .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    database_url: str = "postgresql+asyncpg://argus:argus@postgres:5432/argus"
    redis_url: str = "redis://redis:6379/0"
    qdrant_url: str = "http://qdrant:6333"
    api_token: str = "dev-token"

    # External API base URLs (overridable for tests).
    coingecko_base_url: str = "https://api.coingecko.com/api/v3"
    defillama_base_url: str = "https://api.llama.fi"
    defillama_stablecoins_url: str = "https://stablecoins.llama.fi"
    mempool_base_url: str = "https://mempool.space/api"

    # LLM (zero-cost mode: Gemini free tier primary, Groq free tier fallback).
    llm_provider: str = "gemini"  # gemini | groq | anthropic
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-5"

    # Regulatory RAG.
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_dim: int = 384
    qdrant_regulatory_collection: str = "regulatory"
    rag_top_k: int = 12
    rag_score_cutoff: float = 0.62


settings = Settings()
