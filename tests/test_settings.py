import pytest

from app.core.config import DEV_JWT_SECRET, Settings

URLS = {
    "database_url": "postgresql+asyncpg://insight:insight@localhost:5434/call_insight",
    "redis_url": "redis://localhost:6381/0",
    "rabbitmq_url": "amqp://insight:insight@localhost:5673//",
}


def test_production_refuses_the_dev_jwt_secret() -> None:
    with pytest.raises(ValueError, match="JWT_SECRET"):
        Settings(environment="production", jwt_secret=DEV_JWT_SECRET, **URLS)


def test_production_accepts_its_own_jwt_secret() -> None:
    settings = Settings(environment="production", jwt_secret="a-real-secret", **URLS)

    assert settings.jwt_secret == "a-real-secret"


def test_local_keeps_the_dev_jwt_secret() -> None:
    settings = Settings(**URLS)

    assert settings.environment == "local"
    assert settings.jwt_secret == DEV_JWT_SECRET
