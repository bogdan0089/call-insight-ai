from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEV_JWT_SECRET = "dev-jwt-secret"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    redis_url: str
    rabbitmq_url: str

    db_echo: bool = False
    log_level: str = "INFO"

    storage_dir: str = "storage"

    cors_origins: list[str] = ["http://localhost:3100"]

    anthropic_api_key: str = ""
    voyage_api_key: str = ""

    llm_model: str = "claude-opus-5"
    llm_max_tokens: int = 4000
    llm_timeout_seconds: float = 60.0
    llm_max_retries: int = 3
    llm_input_price_per_mtok: float = 5.0
    llm_output_price_per_mtok: float = 25.0

    environment: str = "local"
    jwt_secret: str = DEV_JWT_SECRET
    jwt_ttl_minutes: int = 60

    frontend_url: str = "http://localhost:3100"

    report_timezone: str = "Europe/Kyiv"
    api_key_touch_seconds: int = 300

    demo_enabled: bool = False
    demo_email: str = "demo@call-insight.local"

    rate_limit_enabled: bool = True
    rate_limit_fail_open: bool = True
    trust_forwarded_for: bool = False

    rate_limits: dict[str, str] = {
        "ip": "300/60",
        "principal": "600/60",
        "login_ip": "20/300",
        "login_email": "5/300",
        "register": "5/3600",
        "resend": "5/3600",
        "verify": "20/600",
        "demo": "30/600",
    }
    email_verification_ttl_hours: int = 24

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "no-reply@call-insight.local"
    smtp_from_name: str = "call insight"
    smtp_use_tls: bool = True
    smtp_timeout_seconds: int = 15

    mail_async: bool = True

    mail_dir: str = "storage/mail"

    @model_validator(mode="after")
    def refuse_dev_secret_in_production(self) -> "Settings":
        if self.environment == "production" and self.jwt_secret == DEV_JWT_SECRET:
            raise ValueError("ENVIRONMENT=production requires its own JWT_SECRET")
        return self


settings = Settings()
