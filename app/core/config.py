from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    redis_url: str
    rabbitmq_url: str

    db_echo: bool = False
    log_level: str = "INFO"

    storage_dir: str = "storage"

    cors_origins: list[str] = ["http://localhost:3100"]

    groq_api_key: str = ""
    anthropic_api_key: str = ""
    voyage_api_key: str = ""

    llm_model: str = "claude-opus-5"
    llm_max_tokens: int = 4000
    llm_timeout_seconds: float = 60.0
    llm_max_retries: int = 3
    llm_input_price_per_mtok: float = 5.0
    llm_output_price_per_mtok: float = 25.0

    telephony_webhook_secret: str = "dev-secret"

    jwt_secret: str = "dev-jwt-secret"
    jwt_ttl_minutes: int = 60

    frontend_url: str = "http://localhost:3100"
    email_verification_ttl_hours: int = 24


settings = Settings()
