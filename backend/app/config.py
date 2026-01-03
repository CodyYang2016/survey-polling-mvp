#changed for mock purposes

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://postgres:postgres@postgres:5432/polling_survey"
    
    # Anthropic API
    anthropic_api_key: str = "not-needed-for-mock"  # Changed default
    
    # Application
    app_env: str = "development"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Session Config
    session_timeout_minutes: int = 30
    max_followup_probes: int = 3
    
    # Mock LLM Mode
    use_mock_llm: bool = True  # Set to True to use mock responses (no API calls)
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()