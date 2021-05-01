"""Minecraft cog."""
import logging
from typing import Union

from discord.ext import commands
from discord_slash import cog_ext
from discord_slash import SlashContext
from discord_slash.utils.manage_commands import create_option
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
    async def tick2second(
        self, ctx: Union[commands.Context, SlashContext], ticks: int
    ) -> None:
        """Convert seconds to tick."""
        if ticks <= 0:
            await ctx.send("Input must be greater then 0")
            return
        try:
            seconds = ticks / 20
        except OverflowError:
            await ctx.send("Input too big.")
            return
        await ctx.send(
            _("It takes {seconds} second for {ticks} to happen.").format(
                seconds=seconds, ticks=ticks
            )
        )

    @commands.group()
    async def convert(self, ctx: Union[commands.Context, SlashContext]) -> None:
        """Convert Minecraft values."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @convert.command()
    async def second(self, ctx: Union[commands.Context, SlashContext], ticks: int):
        """Convert ticks to seconds."""
        if ticks <= 0:
            await ctx.send("Input must be greater then 0")
            return
        try:
            seconds = ticks / 20
        except OverflowError:
            await ctx.send("Input too big.")
            return
        await ctx.send(
            _("It takes {seconds} seconds for {ticks} ticks to happen.").format(
                seconds=seconds, ticks=ticks
            )
        )

    @convert.command()
    async def tick(self, ctx: Union[commands.Context, SlashContext], seconds: float):
        """Convert seconds to tick."""
        if seconds <= 0:
            await ctx.send("Input must be greater then 0")
            return
        ticks = seconds * 20
        await ctx.send(
            _("There are {ticks} ticks in {seconds} seconds").format(
                ticks=ticks, seconds=seconds
            )
        )

    @commands.command()
    async def seed(
        self, ctx: Union[commands.Context, SlashContext], *, text: str
    ) -> None:
        """Convert text to minecraft numerical seed."""
        try:
            int(text)
            await ctx.send(str(int(text)))
            return
        except ValueError:
            pass
        h = 0
        for c in text:
            h = (31 * h + ord(c)) & 0xFFFFFFFF
        await ctx.send(str(((h + 0x80000000) & 0xFFFFFFFF) - 0x80000000))

    @cog_ext.cog_slash(
        name="seed",
        options=[
            create_option(
                name="seed",
                description="Seed in text format to see numerical representation",
                option_type=3,
                required=True,
            )
        ],
    )
    async def slash_seed(self, ctx: SlashContext, *, text: str) -> None:
        await ctx.defer()
        await self.seed(ctx, text)
