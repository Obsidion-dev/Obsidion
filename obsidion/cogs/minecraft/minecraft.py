"""Minecraft cog."""
import logging
from discord.ext import commands
from obsidion.core.i18n import cog_i18n
from obsidion.core.i18n import Translator
from discord_slash import cog_ext

log = logging.getLogger(__name__)

_ = Translator("Minecraft", __file__)


@cog_i18n(_)
class Minecraft(commands.Cog):
    def __init__(self, bot) -> None:
        """Init."""
        self.bot = bot

    @commands.command()
    async def tick2second(self, ctx, ticks: int) -> None:
        """Convert seconds to tick."""
        seconds = ticks / 20
        await ctx.send(
            _("It takes {seconds} second for {ticks} to happen.").format(
                seconds=seconds, ticks=ticks
            )
        )

    @cog_ext.cog_slash(name="tick2second")
    async def slash_tick2second(self, ctx, ticks: int):
        await ctx.defer()
        await self.tick2second(ctx, ticks)

    @commands.command()
    async def second2tick(self, ctx, seconds: float) -> None:
        """Convert ticks to seconds."""
        ticks = seconds * 20
        await ctx.send(
            _("There are {ticks} ticks in {seconds} seconds").format(
                ticks=ticks, seconds=seconds
            )
        )
    
    @cog_ext.cog_slash(name="second2tick")
    async def slash_second2tick(self, ctx, seconds: float):
        await ctx.defer()
        await self.second2tick(ctx, seconds)

    @commands.command()
    async def seed(self, ctx, *, text: str) -> None:
        """Convert text to minecraft numerical seed."""
        h = 0
        for c in text:
            h = (31 * h + ord(c)) & 0xFFFFFFFF
        await ctx.send(((h + 0x80000000) & 0xFFFFFFFF) - 0x80000000)

    @cog_ext.cog_slash(name="seed")
    async def slash_seed(self, ctx, *, text: str):
        await ctx.defer()
        await self.seed(ctx, text)
