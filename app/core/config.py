from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    redis_url: str
    rabbitmq_url: str

    storage_dir: str = "storage"

    groq_api_key: str = ""
    anthropic_api_key: str = ""

    telephony_webhook_secret: str = "dev-secret"

    jwt_secret: str = "dev-jwt-secret"
    jwt_ttl_minutes: int = 60


settings = Settings()
