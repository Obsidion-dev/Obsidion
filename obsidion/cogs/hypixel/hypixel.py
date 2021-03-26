"""Images cog."""
import logging

import discord
from asyncpixel import Hypixel as _Hypixel
from discord.ext import commands
from obsidion.core import get_settings
from obsidion.core.i18n import cog_i18n
from obsidion.core.i18n import Translator

log = logging.getLogger(__name__)

_ = Translator("Hypixel", __file__)


@cog_i18n(_)
class Hypixel(commands.Cog):
    def __init__(self, bot) -> None:
        """Init."""
        self.bot = bot
        self.hypixel = _Hypixel(get_settings().HYPIXEL_API_TOKEN)

    @commands.command()
    async def watchdogstats(self, ctx: commands.Context) -> None:
        """Get the current watchdog statistics."""
        await ctx.channel.trigger_typing()
        data = await self.hypixel.watchdog_stats()
        embed = discord.Embed(title=_("Watchdog Stats"), colour=self.bot.color)
        embed.add_field(
            name=_("Total Bans"), value=f"{(data.watchdog_total + data.staff_total):,}"
        )
        embed.add_field(
            name=_("Watchdog Rolling Daily"), value=f"{data.watchdog_rolling_daily:,}"
        )
        embed.add_field(name=_("Staff Total"), value=f"{data.staff_total:,}")
        embed.add_field(
            name=_("Staff Rolling Daily"), value=f"{data.staff_rolling_daily:,}"
        )
        embed.timestamp = ctx.message.created_at
        await ctx.send(embed=embed)
    @commands.command()
    async def boosters(self, ctx:commands.Context) -> None:
        """Get the current boosters online."""
        await ctx.channel.trigger_typing()
        data = await self.hypixel.boosters()
        embed = discord.Embed(title=_("Boosters"), description=_(f"Total Boosters online: {len(data.boosters)}"), colour=self.bot.color)
        embed.set_author(name=_("Hypixel"), url="https://hypixel.net/forums/skyblock.157/", icon_url="https://hypixel.net/favicon-32x32.png")
        embed.set_thumbnail(url="https://hypixel.net/styles/hypixel-v2/images/header-logo.png")
        embed.timestamp = ctx.message.created_at

        await ctx.send(embed=embed)