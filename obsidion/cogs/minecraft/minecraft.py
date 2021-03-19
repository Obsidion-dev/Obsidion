"""Minecraft cog."""
import json
import logging
from datetime import datetime
from random import choice

import discord
from discord.ext import commands
from obsidion.core import get_settings
from obsidion.core.i18n import cog_i18n
from obsidion.core.i18n import Translator

log = logging.getLogger(__name__)

_ = Translator("Minecraft", __file__)


@cog_i18n(_)
class Minecraft(commands.Cog):
    def __init__(self, bot) -> None:
        """Init."""
        self.bot = bot

    @commands.command()
    async def tick2second(self, ctx: commands.Context, ticks: int) -> None:
        """Convert seconds to tick."""
        seconds = ticks / 20
        await ctx.send(
            _("It takes {seconds} second for {ticks} to happen.").format(
                seconds=seconds, ticks=ticks
            )
        )

    @commands.command()
    async def second2tick(self, ctx: commands.Context, seconds: float) -> None:
        """Convert ticks to seconds."""
        ticks = seconds * 20
        await ctx.send(
            _("There are {ticks} ticks in {seconds} seconds").format(
                ticks=ticks, seconds=seconds
            )
        )

    @commands.command()
    async def seed(self, ctx: commands.Context, *, text: str) -> None:
        """Convert text to minecraft numerical seed."""
        h = 0
        for c in text:
            h = (31 * h + ord(c)) & 0xFFFFFFFF
        await ctx.send(((h + 0x80000000) & 0xFFFFFFFF) - 0x80000000)
