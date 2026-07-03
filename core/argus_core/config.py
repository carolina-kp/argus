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


settings = Settings()
