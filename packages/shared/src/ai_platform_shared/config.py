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

    agent_host: str = "0.0.0.0"
    agent_port: int = 8001
    agent_enabled: bool = True
    agent_max_iterations: int = 25
    agent_max_tool_calls: int = 50
    agent_max_same_tool_calls: int = 10
    agent_max_model_calls: int = 30
    agent_max_runtime_sec: int = 600
    agent_max_context_chars: int = 32_000
    agent_max_tool_result_chars: int = 8_000
    agent_max_history_messages: int = 50
    agent_max_retries: int = 3
    agent_max_retries_per_tool: int = 2
    agent_default_policy: str = "coding"
    agent_tool_timeout_sec: int = 120

    ui_generation_enabled: bool = True
    ui_max_context_chars: int = 24_000
    ui_max_files: int = 40
    ui_max_components: int = 30
    ui_default_validation: str = "build"
    ui_max_generation_files: int = 20

    vision_provider: str = "development_mock"
    vision_model: str = ""
    vision_max_image_bytes: int = 10_485_760  # 10 MiB
    vision_max_width: int = 4096
    vision_max_height: int = 4096
    vision_max_pixels: int = 16_777_216  # 4096*4096
    vision_timeout_sec: int = 120
    screenshot_to_code_enabled: bool = True

    ui_renderer: str = "development_mock"
    ui_render_timeout_sec: int = 120
    visual_validation_enabled: bool = True
    visual_validation_threshold: float = 0.85
    visual_max_iterations: int = 3

    browser_provider: str = "development_mock"
    browser_headless: bool = True
    browser_enabled: bool = True
    browser_timeout_sec: int = 120
    browser_navigation_timeout_sec: int = 30
    browser_action_timeout_sec: int = 15
    browser_max_sessions: int = 10
    browser_max_pages: int = 3
    browser_max_actions: int = 50
    browser_max_navigations: int = 20
    browser_max_screenshots: int = 10
    browser_max_runtime_sec: int = 600
    browser_max_iterations: int = 25
    browser_screenshot_max_bytes: int = 5_242_880
    browser_allowed_domains: str = ""
    browser_blocked_domains: str = ""
    browser_allow_localhost: bool = True
    browser_max_visible_text_chars: int = 8000
    browser_max_elements: int = 100
    browser_max_observation_chars: int = 16000

    multimodal_provider: str = "development_mock"
    multimodal_model: str = ""
    multimodal_max_images: int = 4
    multimodal_max_pixels: int = 16_777_216
    multimodal_max_batch_size: int = 8
    multimodal_max_context_tokens: int = 8192
    multimodal_max_output_tokens: int = 4096
    multimodal_timeout_sec: int = 120
    multimodal_device: str = "auto"
    multimodal_dtype: str = "auto"
    vision_use_multimodal: bool = False

    tools_enabled: bool = True
    tool_max_file_size: int = 1_048_576
    tool_max_output_chars: int = 32_000
    tool_max_search_results: int = 50
    tool_max_context_chars: int = 16_000
    tool_write_enabled: bool = True
    terminal_enabled: bool = True
    terminal_timeout_sec: int = 120
    terminal_max_output_chars: int = 32_000
    terminal_allowed_commands: str = (
        "python,pytest,ruff,node,npm,npx,pnpm,yarn,git,pip,uv,make,cargo,go"
    )
    terminal_denied_commands: str = "rm,del,format,shutdown,reboot,diskpart,reg,curl,wget"
    diagnostics_commands: str = "ruff check .,pytest -q"

    eval_max_samples: int = 100
    eval_max_runtime_sec: int = 600
    eval_max_model_calls: int = 200
    eval_max_tokens: int = 100_000
    eval_sample_retries: int = 1

    rate_limit_rpm: int = 60
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    @field_validator("model_provider", "vision_provider", "ui_renderer", "multimodal_provider")
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
    def terminal_allowed_commands_list(self) -> list[str]:
        return [c.strip().lower() for c in self.terminal_allowed_commands.split(",") if c.strip()]

    @property
    def terminal_denied_commands_list(self) -> list[str]:
        return [c.strip().lower() for c in self.terminal_denied_commands.split(",") if c.strip()]

    @property
    def diagnostics_commands_list(self) -> list[str]:
        return [c.strip() for c in self.diagnostics_commands.split(",") if c.strip()]

    @property
    def browser_allowed_domains_list(self) -> list[str]:
        return [d.strip() for d in self.browser_allowed_domains.split(",") if d.strip()]

    @property
    def browser_blocked_domains_list(self) -> list[str]:
        return [d.strip() for d in self.browser_blocked_domains.split(",") if d.strip()]

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
