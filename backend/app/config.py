from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Database / Core
    database_url: str = Field(
        default="postgresql://postgres:postgres@postgres:5432/polling_survey",
        validation_alias="DATABASE_URL",
    )

    # Anthropic
    anthropic_api_key: str = Field(
        default="not-needed-for-mock",
        validation_alias="ANTHROPIC_API_KEY",
    )

    # Mock LLM Mode
    use_mock_llm: bool = Field(
        default=False,
        validation_alias="USE_MOCK_LLM",
    )

    # Application
    app_env: str = Field(default="development", validation_alias="APP_ENV")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    api_host: str = Field(default="0.0.0.0", validation_alias="API_HOST")
    api_port: int = Field(default=8000, validation_alias="API_PORT")

    # Session Config
    session_timeout_minutes: int = Field(default=30, validation_alias="SESSION_TIMEOUT_MINUTES")
    max_followup_probes: int = Field(default=3, validation_alias="MAX_FOLLOWUP_PROBES")

    # API Safety Settings
    api_timeout_seconds: float = Field(default=30.0, validation_alias="API_TIMEOUT_SECONDS")
    api_max_retries: int = Field(default=3, validation_alias="API_MAX_RETRIES")
    max_cost_per_session_usd: float = Field(default=0.50, validation_alias="MAX_COST_PER_SESSION_USD")

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()


settings = Settings()

# DEBUG - Remove after fixing
print("="*60)
print(f"USE_MOCK_LLM setting: {settings.use_mock_llm}")
print(f"ANTHROPIC_API_KEY set: {bool(settings.anthropic_api_key and settings.anthropic_api_key != 'not-needed-for-mock')}")
print("="*60)
