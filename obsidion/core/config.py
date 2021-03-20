"""Settings management for the bot."""
import logging
from functools import lru_cache
from uuid import UUID

from pydantic import BaseSettings
from pydantic import HttpUrl
from pydantic import PositiveInt
from pydantic import PostgresDsn
from pydantic import RedisDsn
from pydantic.color import Color

log = logging.getLogger("obsidion")


class PlayerNotExist(Exception):
    """Custom API Error."""

    pass


class Settings(BaseSettings):
    """Bot config settings."""

    DISCORD_TOKEN: str = None
    API_URL: HttpUrl = "https://api.obsidion-dev.com/api/v1"
    HYPIXEL_API_TOKEN: UUID = None
    ACTIVITY: str = "for @Obsidion help"
    DEFAULT_PREFIX: str = "/"
    STACK_TRACE_CHANNEL: PositiveInt = None
    DB: PostgresDsn = None
    REDIS: RedisDsn = None
    DEV: bool = False
    COLOR: Color = None

    class Config:
        """Config for pydantic."""

        # Env will always take priority and is recommended for production
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get settings object and cache it."""
    return Settings()
