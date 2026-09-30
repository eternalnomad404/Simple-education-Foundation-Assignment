from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict

_base_config = SettingsConfigDict(
        env_file="./.env",
        env_ignore_empty=True,
        extra="ignore"
    )

class AppSettings(BaseSettings):
    APP_NAME: str = "Communicator"
    APP_DOMAIN: str = "localhost:8000"

    model_config = _base_config

class DatabaseSettings(BaseSettings):
    POSTGRES_PASSWORD: str
    POSTGRES_USERNAME: str
    POSTGRES_SERVER: str
    POSTGRES_PORT: int
    POSTGRES_DB: str

    REDIS_HOST: str
    REDIST_PORT: int

    @property
    def POSTGRES_URL(self) -> str:
        password = quote_plus(self.POSTGRES_PASSWORD)

        return (
            f"postgresql+asyncpg://{self.POSTGRES_USERNAME}:"
            f"{password}@"
            f"{self.POSTGRES_SERVER}:"
            f"{self.POSTGRES_PORT}/"
            f"{self.POSTGRES_DB}"
        )

    model_config = _base_config


class SecuritySettings(BaseSettings):
    JWT_SECRET: str
    JWT_ALGORITHM: str

    model_config = _base_config

class WebhookSettings(BaseSettings):
    WEBHOOK_SECRET: str

    model_config = _base_config

db_settings = DatabaseSettings()
app_settinggs = AppSettings()
security_settings = SecuritySettings()
webhook_settings = WebhookSettings()