"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AI_PLATFORM_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    secret_key: str = "dev-secret-key-change-in-production-min-32-chars"

    database_url: str = "mysql+pymysql://aiplatform:aiplatform@localhost:3306/aiplatform"
    database_pool_size: int = 10
    redis_url: str = "redis://localhost:6379/0"

    ai_api_host: str = "0.0.0.0"
    ai_api_port: int = 8000

    # Provider selection: development_mock | mock | local | proprietary
    model_provider: str = "development_mock"
    default_model: str = "development-mock-v1"

    # Local model configuration
    model_id: str = ""
    model_path: str = ""
    model_device: str = "auto"
    model_dtype: str = "auto"
    model_max_context: int = 4096
    model_trust_remote_code: bool = False
    model_generation_timeout_sec: int = 120
    model_generation_max_tokens: int = 1024
    model_generation_temperature: float = 0.7
    model_generation_top_p: float = 1.0

    rate_limit_rpm: int = 60
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    @field_validator("model_provider")
    @classmethod
    def normalize_provider(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized == "mock":
            return "development_mock"
        return normalized

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.env == "production"

    @property
    def resolved_model_ref(self) -> str:
        return self.model_path or self.model_id or self.default_model

    def validate_production_provider(self) -> None:
        if self.is_production and self.model_provider == "development_mock":
            raise ValueError(
                "DevelopmentMockProvider cannot be used in production. "
                "Set AI_PLATFORM_MODEL_PROVIDER=local or proprietary."
            )


@lru_cache
def get_settings() -> Settings:
    return Settings()
