"""Images cog."""
import logging
import datetime

import discord
from asyncpixel import Hypixel as _Hypixel
from discord.ext import commands
from obsidion.core import get_settings
from obsidion.core.i18n import cog_i18n
from obsidion.core.i18n import Translator
from obsidion.core.utils.chat_formatting import humanize_timedelta

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
    @commands.command()
    async def playercount(self, ctx: commands.Context) -> None:
        """Get the current players online."""
        await ctx.channel.trigger_typing()
        data = await self.hypixel.player_count()
        embed = discord.Embed(title=_("Players Online"), description=_(f"Total players online: {data}"), colour=self.bot.color)
        embed.set_author(name=_("Hypixel"), url="https://hypixel.net/forums/skyblock.157/", icon_url="https://hypixel.net/favicon-32x32.png")
        embed.set_thumbnail(url="https://hypixel.net/styles/hypixel-v2/images/header-logo.png")
        embed.timestamp = ctx.message.created_at

        await ctx.send(embed=embed)
    @commands.command()
    async def skyblocknews(self, ctx: commands.Context) -> None:
        """Get current news for skyblock."""
        await ctx.channel.trigger_typing()
        data = await self.hypixel.news()
        embed = discord.Embed(title=_("Skyblock News"), description=_(f"There are currently {len(data)} news articles."), colour=self.bot.color)
        embed.set_author(name=_("Hypixel"), url="https://hypixel.net/forums/skyblock.157/", icon_url="https://hypixel.net/favicon-32x32.png")
        embed.set_thumbnail(url="https://hypixel.net/styles/hypixel-v2/images/header-logo.png")

        for i in range(len(data)):
            embed.add_field(name=_(f"{data[i].title}"), value=f"[{data[i].text}]({data[i].link})")

        embed.timestamp = ctx.message.created_at

        await ctx.send(embed=embed)
    @commands.command()
    async def playerstatus(self, ctx: commands.Context, username: str) -> None:
        """Get the current status of an online player."""
        await ctx.channel.trigger_typing()
        
        player_data = await self.bot.mojang_player(ctx.author, username)
        uuid = player_data["uuid"]

        data = await self.hypixel.player_status(uuid)

        if data.online == False:
            await ctx.send("That player is not currently online.")
            return
        else:
            embed = discord.Embed(title=_("Player Status"), description=_(f"Current status of Player {username}"), colour=self.bot.color)
            embed.set_author(name=_("Hypixel"), url="https://hypixel.net/forums/skyblock.157/", icon_url="https://hypixel.net/favicon-32x32.png")
            embed.set_thumbnail(url=f"https://visage.surgeplay.com/bust/{uuid}")
            
            embed.add_field(name=_("Current game: "), value=_(f"{data.game_type.CleanName}"))
            embed.add_field(name=_("Current game mode: "), value=_(f"{data.mode}"))

            embed.timestamp = ctx.message.created_at

        await ctx.send(embed=embed)
    @commands.command()
    async def playerfriends(self, ctx: commands.Context, username: str) -> None:
        """Get the current friends of a player."""
        await ctx.channel.trigger_typing()
        player_data = await self.bot.mojang_player(ctx.author, username)
        uuid = player_data["uuid"]
        
        data = await self.hypixel.player_friends(uuid)

        embed = discord.Embed(title=_("Player Friends"), description=_(f"Current Friends for {username}"), colour=self.bot.color)
        embed.set_author(name=_("Hypixel"), url="https://hypixel.net/forums/skyblock.157/", icon_url="https://hypixel.net/favicon-32x32.png")
        embed.set_thumbnail(url=f"https://visage.surgeplay.com/bust/{uuid}")
        embed.timestamp = ctx.message.created_at


        for i in range(len(data)):
            if data[i].uuid_receiver == uuid:
                friendUsername = await self.bot.mojang_player(ctx.author, data[i].uuid_sender)
            else:
                friendUsername = await self.bot.mojang_player(ctx.author, data[i].uuid_receiver)
            
            friendUsername = friendUsername["username"]
            
            delta = datetime.datetime.now(tz=datetime.timezone.utc) - data[i].started
            friendStarted = humanize_timedelta(timedelta=delta)
            friendStartedSplit = friendStarted.split(", ")
            friendStarted = friendStartedSplit[0] + ", " + friendStartedSplit[1]

            embed.add_field(name=_(f"{friendUsername}"), value =_(f"Been friends for {friendStarted}"))

        await ctx.send(embed=embed)  