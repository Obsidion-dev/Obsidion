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

    DISCORD_TOKEN: str
    API_URL: HttpUrl
    HYPIXEL_API_TOKEN: UUID
    ACTIVITY: str = "for @Obsidion help"
    DEFAULT_PREFIX: str = "mc?"
    STACK_TRACE_CHANNEL: PositiveInt
    DB: PostgresDsn
    REDIS: RedisDsn
    DEV: bool = False
    COLOR: Color = Color("0x00FF00")

    class Config:
        """Config for pydantic."""

        # Env will always take priority and is recommended for production
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get settings object and cache it."""
    return Settings()
