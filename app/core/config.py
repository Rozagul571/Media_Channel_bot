from functools import lru_cache
from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    # -------- TELEGRAM --------
    TELEGRAM_API_ID: int
    TELEGRAM_API_HASH: str
    TELEGRAM_PHONE: str
    TELEGRAM_BOT_TOKEN: str

    SOURCE_CHANNEL: str
    TARGET_CHANNEL: str

    # -------- OPENAI --------
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"

    # -------- DATABASE --------
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/pipeline.db"

    # -------- PIPELINE --------
    POLL_INTERVAL_SECONDS: int = 60
    FETCH_LIMIT: int = 30
    MAX_RETRIES: int = 3
    RETRY_DELAY_SECONDS: int = 5
    MIN_TEXT_LENGTH: int = 20

    # -------- LOGGING --------
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/pipeline.log"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )

    @field_validator("SOURCE_CHANNEL", "TARGET_CHANNEL")
    def clean_channel_name(cls, v: str) -> str:
        v = v.replace("https://t.me/", "").replace("t.me/", "")
        return v.lstrip("@")

    def get_session_path(self) -> str:
        path = Path("./data/user_session")
        path.parent.mkdir(parents=True, exist_ok=True)
        return str(path)

    def get_bot_session_path(self) -> str:
        path = Path("./data/bot_session")
        path.parent.mkdir(parents=True, exist_ok=True)
        return str(path)

    def get_database_url(self) -> str:
        """Return database URL"""
        return self.DATABASE_URL

@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()