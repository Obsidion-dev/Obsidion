from typing import List
from typing import Optional
from typing import Union
from typing import Dict
import json

import discord

from .config import get_settings


class PrefixManager:
    def __init__(self, bot):
        self._bot = bot

    async def get_prefixes(self, guild: Optional[discord.Guild] = None) -> List[str]:
        gid: Optional[int] = guild.id if guild else None
        if gid is None:
            return [get_settings().DEFAULT_PREFIX]

        key = f"prefix_{gid}"
        redis = await self._bot.redis.exists(key)
        if redis:
            prefix = (await self._bot.redis.get(key)).decode("UTF-8")
        else:
            db_prefix = await self._bot.db.fetchval(
                "SELECT prefix FROM guild WHERE id = $1", gid
            )
            if db_prefix:
                prefix = db_prefix
            else:
                prefix = get_settings().DEFAULT_PREFIX
        await self._bot.redis.set(key, prefix, expire=28800)
        return [str(prefix)]

    async def set_prefixes(
        self,
        guild: discord.Guild,
        prefix: Optional[str] = None,
    ):
        gid = guild.id

        key = f"prefix_{gid}"
        if prefix is None:
            prefix = get_settings().DEFAULT_PREFIX
        elif await self._bot.db.fetch("SELECT prefix FROM guild WHERE id = $1", gid):
            await self._bot.db.execute(
                "UPDATE guild SET prefix = $1 WHERE id = $2", prefix, gid
            )
        else:
            await self._bot.db.execute(
                "INSERT INTO guild (id, prefix) VALUES ($1, $2)",
                gid,
                prefix,
            )
        await self._bot.redis.set(key, prefix, expire=28800)


class I18nManager:
    def __init__(self, bot):
        self._bot = bot

    async def get_locale(self, guild: Union[discord.Guild, None]) -> str:
        """Get the guild locale from the cache"""
        if not guild:
            return "en-US"
        gid = guild.id
        key = f"locale_{gid}"
        redis = await self._bot.redis.exists(key)
        if redis:
            locale = (await self._bot.redis.get(key)).decode("UTF-8")
        else:
            db_locale = await self._bot.db.fetchval(
                "SELECT locale FROM guild WHERE id = $1", gid
            )
            if db_locale:
                locale = db_locale
            else:
                locale = "en-US"
        await self._bot.redis.set(key, locale, expire=28800)

        return locale

    async def set_locale(self, guild: discord.Guild, locale: Union[str, None]) -> None:
        """Set the locale in the config and cache"""
        gid = guild.id

        key = f"locale_{gid}"
        if await self._bot.db.fetch("SELECT locale FROM guild WHERE id = $1", gid):
            await self._bot.db.execute(
                "UPDATE guild SET locale = $1 WHERE id = $2", locale, gid
            )
        else:
            await self._bot.db.execute(
                "INSERT INTO guild (id, locale) VALUES ($1, $2)",
                gid,
                locale,
            )
        await self._bot.redis.set(key, locale, expire=28800)

    async def get_regional_format(
        self, guild: Union[discord.Guild, None]
    ) -> Optional[str]:
        """Get the regional format from the cache"""
        if not guild:
            return "en-US"
        gid = guild.id
        key = f"regional_{gid}"
        redis = await self._bot.redis.exists(key)
        if redis:
            regional = (await self._bot.redis.get(key)).decode("UTF-8")
        else:
            db_regional = await self._bot.db.fetchval(
                "SELECT regional FROM guild WHERE id = $1", gid
            )
            if db_regional:
                regional = db_regional
            else:
                regional = "en-US"
        await self._bot.redis.set(key, regional, expire=28800)

        return regional

    async def set_regional_format(
        self, guild: Union[discord.Guild, None], regional_format: Union[str, None]
    ) -> None:
        """Set the regional format in the config and cache"""
        gid = guild.id

        key = f"regional_{gid}"
        if await self._bot.db.fetch("SELECT regional FROM guild WHERE id = $1", gid):
            await self._bot.db.execute(
                "UPDATE guild SET regional = $1 WHERE id = $2", regional_format, gid
            )
        else:
            await self._bot.db.execute(
                "INSERT INTO guild (id, regional) VALUES ($1, $2)",
                gid,
                regional_format,
            )
        await self._bot.redis.set(key, regional_format, expire=28800)


class RconManager:
    def __init__(self, bot):
        self._bot = bot

    async def get_rcon(
        self, guild: Optional[discord.Guild] = None
    ) -> Union[Dict[str, Union[str, int]], None]:
        """Get rcon data."""
        if guild is None:
            return None
        gid = guild.id
        key = f"rcon_{gid}"
        redis = await self._bot.redis.exists(key)
        if redis:
            rcon = json.load((await self._bot.redis.get(key)).decode("UTF-8"))
        else:
            rcon_details = await self._bot.db.fetchrow(
                "SELECT * FROM rcon WHERE id = $1", gid
            )
            rcon = {
                "server": rcon_details.get("server"),
                "password": rcon_details.get("password"),
                "port": rcon_details.get("port"),
            }

        await self._bot.redis.set(key, json.dump(rcon), expire=28800)
        return rcon

    async def set_rcon(
        self, guild: discord.Guild, server: str, password: str, port: int
    ) -> None:
        """Set rcon."""
        gid = guild.id

        key = f"rcon_{gid}"
        if await self._bot.db.fetch("SELECT * FROM rcon WHERE id = $1", gid):
            await self._bot.db.execute(
                "UPDATE rcon SET server = $1, password = $2, port = $3 WHERE id = $4",
                server,
                password,
                port,
                gid,
            )
        else:
            await self._bot.db.execute(
                "INSERT INTO guild (id, server, password, port) VALUES ($1, $2, $3, $4)",
                gid,
                server,
                password,
                port,
            )
        rcon = {
            "server": server,
            "password": password,
            "port": port,
        }
        await self._bot.redis.set(key, json.dump(rcon), expire=28800)

