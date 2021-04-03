"""Images cog."""
import io
import json
import logging
from datetime import datetime
from typing import Optional, Tuple
import base64

import discord
from discord.ext import commands
from obsidion.core import get_settings
from obsidion.core.i18n import cog_i18n
from obsidion.core.i18n import Translator
from discord_slash import cog_ext
from discord_slash.utils.manage_commands import create_option
from asyncrcon import AsyncRCON, AuthenticationException

log = logging.getLogger(__name__)

_ = Translator("Rcon", __file__)


@cog_i18n(_)
class Rcon(commands.Cog):
    def __init__(self, bot) -> None:
        """Init."""
        self.bot = bot

    @commands.command()
    async def cmd(self, ctx, *, command):
        await ctx.trigger_typing()

        try:
            _rcon = await self.rcon(ctx.guild.id)
        except AuthenticationException:
            await ctx.send(_("Login failed: Unauthorized."))
            return

        res = await _rcon.command(f"/{command}")
        await ctx.send(res)

        _rcon.close()

    @cog_ext.cog_slash(name="say")
    async def slash_command(self, ctx, *, command):
        await ctx.defer()
        await self.say(ctx, command)

    @commands.command()
    async def say(self, ctx, *, message):
        await ctx.trigger_typing()

        try:
            _rcon = await self.rcon(ctx.guild.id)
        except AuthenticationException:
            await ctx.send(_("Login failed: Unauthorized."))
            return

        res = await _rcon.command(f"say {message}")
        await ctx.send(res)

        _rcon.close()

    @cog_ext.cog_slash(name="say")
    async def slash_say(self, ctx, *, message):
        await ctx.defer()
        await self.say(ctx, message)

    async def rcon(self, ctx) -> AsyncRCON:
        data = await self.bot._rcon_cache.get_rcon(ctx.guild.id)
        if ctx.author.roles
        _rcon = AsyncRCON(data["address"], data["port"], data["password"])
        await _rcon.open_connection()

        return _rcon