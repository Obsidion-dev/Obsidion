"""Main bot file."""
import json
import socket
import sys
from enum import IntEnum
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import aiohttp
import aioredis
import asyncpg
import discord
from discord.ext.commands import AutoShardedBot
from discord.ext.commands import when_mentioned_or

from .config import get_settings
from .config import PlayerNotExist
from .core_commands import Core
from .events import Events
from .global_checks import init_global_checks
from .settings_cache import AccountManager
from .settings_cache import GuildManager
from .settings_cache import I18nManager
from .settings_cache import PrefixManager


class Obsidion(AutoShardedBot):
    """Main bot class."""

    redis: aioredis.Redis
    http_session: aiohttp.ClientSession
    _connector: aiohttp.TCPConnector
    _resolver: aiohttp.AsyncResolver

    def __init__(self, *args, **kwargs) -> None:
        """Initialise bot with args passed through."""
        self._shutdown_mode = ExitCodes.CRITICAL
        self.uptime = None
        color = get_settings().COLOR.as_rgb_tuple()
        self.color = discord.Color.from_rgb(color[0], color[1], color[2])
        self._last_exception = None
        self._invite = None
        self.db = None

        self._prefix_cache = PrefixManager(self)
        self._i18n_cache = I18nManager(self)
        self._account_cache = AccountManager(self)
        self._guild_cache = GuildManager(self)

        async def prefix_manager(bot, message: discord.Message) -> List[str]:
            prefixes = await self._prefix_cache.get_prefixes(message.guild)
            return when_mentioned_or(*prefixes)(bot, message)

        kwargs["command_prefix"] = prefix_manager
        super().__init__(*args, **kwargs)

    async def pre_flight(self) -> None:
        init_global_checks(self)

        self.redis = await aioredis.create_redis_pool(str(get_settings().REDIS))
        self.db = await asyncpg.create_pool(str(get_settings().DB))
        self._resolver = aiohttp.AsyncResolver()
        # Use AF_INET as its socket family to prevent HTTPS related
        # problems both locally and in production.
        self._connector = aiohttp.TCPConnector(
            resolver=self._resolver,
            family=socket.AF_INET,
        )

        # Client.login() will call HTTPClient.static_login()
        # which will create a session using this connector attribute.
        self.http_session = aiohttp.ClientSession(connector=self._connector)

        # Load important cogs
        self.add_cog(Events(self))
        self.add_cog(Core(self))
        if get_settings().DEV:
            from .dev_commands import Dev

            self.add_cog(Dev(self))

        # load cogs
        self.load_extension("obsidion.cogs.images")
        self.load_extension("obsidion.cogs.info")
        self.load_extension("obsidion.cogs.hypixel")
        self.load_extension("obsidion.cogs.news")
        self.load_extension("obsidion.cogs.fun")
        self.load_extension("obsidion.cogs.minecraft")
        self.load_extension("obsidion.cogs.config")
        self.load_extension("obsidion.cogs.facts")
        self.load_extension("obsidion.cogs.servers")

        if get_settings().BOTLIST_POSTING:
            self.load_extension("obsidion.cogs.botlist")

    async def start(self, *args, **kwargs):
        """
        Overridden start which ensures cog load and other
        pre-connection tasks are handled
        """
        await self.pre_flight()
        return await super().start(*args, **kwargs)

    async def message_eligible_as_command(self, message: discord.Message) -> bool:
        """
        Runs through the things which apply globally about commands
        to determine if a message may be responded to as a command.

        This can't interact with permissions as permissions is hyper-local
        with respect to command objects, create command objects for this
        if that's needed.

        This also does not check for prefix or command conflicts,
        as it is primarily designed for non-prefix based response handling
        via on_message_without_command

        Parameters
        ----------
        message
            The message object to check

        Returns
        -------
        bool
            Whether or not the message is eligible to be treated as a command.
        """

        channel = message.channel
        guild = message.guild

        if message.author.bot:
            return False

        if guild:
            if not channel.permissions_for(guild.me).send_messages:
                return False

        return True

    async def set_prefixes(
        self, guild: discord.Guild, prefix: Optional[str] = None
    ) -> None:
        """
        Set global/server prefixes.

        If ``guild`` is not provided (or None is passed), this
        will set the global prefixes.

        Parameters
        ----------
        prefixes : str
            The prefixes you want to set. Passing empty list will
            reset prefixes for the ``guild``
        guild : Optional[discord.Guild]
            The guild you want to set the prefixes for. Omit
            (or pass None) to set the global prefixes

        Raises
        ------
        TypeError
            If ``prefixes`` is not a list of strings
        ValueError
            If empty list is passed to ``prefixes`` when setting global prefixes
        """
        await self._prefix_cache.set_prefixes(guild=guild, prefix=prefix)

    async def shutdown(self, *, restart: Optional[bool] = False) -> None:
        """Gracefully quit Obsidion.

        The program will exit with code :code:`0` by default.

        Parameters
        ----------
        restart : bool
            If :code:`True`, the program will exit with code :code:`26`. If the
            launcher sees this, it will attempt to restart the bot.

        """
        if not restart:
            self._shutdown_mode = ExitCodes.SHUTDOWN
        else:
            self._shutdown_mode = ExitCodes.RESTART

        await self.close()
        sys.exit(self._shutdown_mode)

    async def mojang_player(
        self, user: discord.User, username: Optional[str] = None
    ) -> Dict[str, Any]:
        """Takes in an mc username and tries to convert it to a mc uuid.

        Args:
            username (str): username of player which uuid will be from
            bot (Obsidion): Obsidion bot

        Returns:
            str: uuid of player
        """
        if username is None:
            _uuid = await self._account_cache.get_account(user)
            if _uuid is None:
                raise PlayerNotExist()
            uuid = str(_uuid)
        else:
            username_key = f"username_{username}"
            if await self.redis.exists(username_key):
                uuid = str((await self.redis.get(username_key)).decode("UTF-8"))
            else:
                uuid = str(username)
        data: Optional[Dict[str, Any]]
        key = f"player_{str(uuid)}"
        if await self.redis.exists(key):
            data = json.loads(await self.redis.get(key))
        else:
            url = f"https://api.ashcon.app/mojang/v2/user/{str(uuid)}"
            async with self.http_session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                else:
                    data = None
        if data is not None:
            uuid = data["uuid"]
        key = f"player_{uuid}"
        await self.redis.set(key, json.dumps(data), expire=28800)
        if data is None:
            raise PlayerNotExist()
        username_key = f"username_{data['username']}"
        await self.redis.set(username_key, str(uuid), expire=28800)
        return data


class ExitCodes(IntEnum):
    # This needs to be an int enum to be used
    # with sys.exit
    CRITICAL = 1
    SHUTDOWN = 0
    RESTART = 26
