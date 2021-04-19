"""Images cog."""
import datetime
import logging
from typing import Optional

import discord
from asyncpixel import Hypixel as _Hypixel
from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.utils.manage_commands import create_option
from dpymenus import Page
from dpymenus import PaginatedMenu
from obsidion.core import get_settings
from obsidion.core.i18n import cog_i18n
from obsidion.core.i18n import Translator
from obsidion.core.utils.chat_formatting import humanize_timedelta
from obsidion.core.utils.utils import divide_array


log = logging.getLogger(__name__)

_ = Translator("Hypixel", __file__)


@cog_i18n(_)
class Hypixel(commands.Cog):
    def __init__(self, bot) -> None:
        """Init."""
        self.bot = bot
        self.hypixel = _Hypixel(get_settings().HYPIXEL_API_TOKEN)

    @commands.command()
    async def watchdogstats(self, ctx) -> None:
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

    @cog_ext.cog_slash(name="watchdogstats")
    async def slash_watchdogstats(self, ctx):
        """Get the current watchdog statistics."""
        await ctx.defer()
        await self.watchdogstats(ctx)

    @commands.command()
    async def boosters(self, ctx) -> None:
        """Get the current boosters online."""
        await ctx.channel.trigger_typing()
        data = await self.hypixel.boosters()
        embed = discord.Embed(
            title=_("Boosters"),
            description=_(f"Total Boosters online: {len(data.boosters)}"),
            colour=self.bot.color,
        )
        embed.set_author(
            name=_("Hypixel"),
            url="https://hypixel.net/forums/skyblock.157/",
            icon_url="https://hypixel.net/favicon-32x32.png",
        )
        embed.set_thumbnail(
            url="https://hypixel.net/styles/hypixel-v2/images/header-logo.png"
        )
        embed.timestamp = ctx.message.created_at

        await ctx.send(embed=embed)

    @cog_ext.cog_slash(name="boosters")
    async def slash_boosters(self, ctx):
        """Get the current boosters online."""
        await ctx.defer()
        await self.boosters(ctx)

    @commands.command()
    async def playercount(self, ctx) -> None:
        """Get the current players online."""
        await ctx.channel.trigger_typing()
        data = await self.hypixel.player_count()
        embed = discord.Embed(
            title=_("Players Online"),
            description=_(f"Total players online: {data}"),
            colour=self.bot.color,
        )
        embed.set_author(
            name=_("Hypixel"),
            url="https://hypixel.net/forums/skyblock.157/",
            icon_url="https://hypixel.net/favicon-32x32.png",
        )
        embed.set_thumbnail(
            url="https://hypixel.net/styles/hypixel-v2/images/header-logo.png"
        )
        embed.timestamp = ctx.message.created_at

        await ctx.send(embed=embed)

    @cog_ext.cog_slash(name="playercount")
    async def slash_playercount(self, ctx):
        """Get the current players online."""
        await ctx.defer()
        await self.playercount(ctx)

    @commands.command()
    async def skyblocknews(self, ctx) -> None:
        """Get current news for skyblock."""
        await ctx.channel.trigger_typing()
        data = await self.hypixel.news()
        embed = discord.Embed(
            title=_("Skyblock News"),
            description=_(f"There are currently {len(data)} news articles."),
            colour=self.bot.color,
        )
        embed.set_author(
            name=_("Hypixel"),
            url="https://hypixel.net/forums/skyblock.157/",
            icon_url="https://hypixel.net/favicon-32x32.png",
        )
        embed.set_thumbnail(
            url="https://hypixel.net/styles/hypixel-v2/images/header-logo.png"
        )

        for i in range(len(data)):
            embed.add_field(
                name=_(f"{data[i].title}"), value=f"[{data[i].text}]({data[i].link})"
            )

        embed.timestamp = ctx.message.created_at

        await ctx.send(embed=embed)

    @cog_ext.cog_slash(name="skyblocknews")
    async def slash_skyblocknews(self, ctx):
        """Get current news for skyblock."""
        await ctx.defer()
        await self.skyblocknews(ctx)

    @commands.command()
    async def playerstatus(self, ctx, username: Optional[str] = None) -> None:
        """Get the current status of an online player."""
        await ctx.channel.trigger_typing()

        player_data = await self.bot.mojang_player(ctx.author, username)
        uuid = player_data["uuid"]

        data = await self.hypixel.player_status(uuid)

        if data.online == False:
            await ctx.send("That player is not currently online.")
            return
        else:
            embed = discord.Embed(
                title=_("Player Status"),
                description=_(f"Current status of Player {username}"),
                colour=self.bot.color,
            )
            embed.set_author(
                name=_("Hypixel"),
                url="https://hypixel.net/forums/skyblock.157/",
                icon_url="https://hypixel.net/favicon-32x32.png",
            )
            embed.set_thumbnail(url=f"https://visage.surgeplay.com/bust/{uuid}")

            embed.add_field(
                name=_("Current game: "), value=_(f"{data.game_type.CleanName}")
            )
            embed.add_field(name=_("Current game mode: "), value=_(f"{data.mode}"))

            embed.timestamp = ctx.message.created_at

        await ctx.send(embed=embed)

    @cog_ext.cog_slash(
        name="playerstatus",
        options=[
            create_option(
                name="username",
                description="Username of account defaults to linked account.",
                option_type=3,
                required=False,
            )
        ],
    )
    async def slash_playerstatus(self, ctx, username=None):
        """Get the current status of an online player."""
        await ctx.defer()
        await self.playerstatus(ctx, username)

    @commands.command()
    async def playerfriends(self, ctx, username: Optional[str] = None) -> None:
        """Get the current friends of a player."""
        await ctx.channel.trigger_typing()
        player_data = await self.bot.mojang_player(ctx.author, username)
        uuid = player_data["uuid"]

        data = await self.hypixel.player_friends(uuid)

        embed = discord.Embed(
            title=_("Player Friends"),
            description=_(f"Current Friends for {username}"),
            colour=self.bot.color,
        )
        embed.set_author(
            name=_("Hypixel"),
            url="https://hypixel.net/forums/skyblock.157/",
            icon_url="https://hypixel.net/favicon-32x32.png",
        )
        embed.set_thumbnail(url=f"https://visage.surgeplay.com/bust/{uuid}")
        embed.timestamp = ctx.message.created_at

        for i in range(len(data)):
            if str(data[i].uuid_receiver) == str(uuid):
                friendUsername = await self.bot.mojang_player(
                    ctx.author, data[i].uuid_sender
                )
            else:
                friendUsername = await self.bot.mojang_player(
                    ctx.author, data[i].uuid_receiver
                )

            friendUsername = friendUsername["username"]

            delta = datetime.datetime.now(tz=datetime.timezone.utc) - data[i].started
            friendStarted = humanize_timedelta(timedelta=delta)
            friendStartedSplit = friendStarted.split(", ")
            friendStarted = friendStartedSplit[0] + ", " + friendStartedSplit[1]

            embed.add_field(
                name=_(f"{friendUsername}"),
                value=_(f"Been friends for {friendStarted}"),
            )

        await ctx.send(embed=embed)

    @cog_ext.cog_slash(
        name="playerfriends",
        options=[
            create_option(
                name="username",
                description="Username of account defaults to linked account.",
                option_type=3,
                required=False,
            )
        ],
    )
    async def slash_playerfriends(self, ctx, username=None):
        """Get the current friends of a player."""
        await ctx.defer()
        await self.playerfriends(ctx, username)

    @commands.command()
    async def bazaar(self, ctx) -> None:
        """Get Bazaar NPC stats."""
        await ctx.channel.trigger_typing()

        menu = PaginatedMenu(ctx)
        data = await self.hypixel.bazaar()
        split = list(divide_array(data.bazaar_items, 15))
        pagesend = []

        for bazaarloop in range(len(split)):
            pagebazaar = Page(
                title=_("Bazaar NPC Stats"),
                description=_(f"Page {bazaarloop + 1} of {(len(split))}"),
                color=self.bot.color,
            )
            pagebazaar.set_author(
                name=_("Hypixel"), icon_url="https://hypixel.net/favicon-32x32.png"
            )
            pagebazaar.set_thumbnail(
                url="https://hypixel.net/styles/hypixel-v2/images/header-logo.png"
            )
            for item in range(len(split[bazaarloop])):
                name = split[bazaarloop][item].product_id.replace("_", " ").title()
                sellprice = round(split[bazaarloop][item].quick_status.sell_price)
                buyprice = round(split[bazaarloop][item].quick_status.buy_price)
                pagebazaar.add_field(
                    name=_(name),
                    value=_(f"Sell Price: {sellprice} \n Buy Price: {buyprice}"),
                )
            pagesend.append(pagebazaar)

        menu.add_pages(pagesend)
        menu.set_timeout(90)

        await menu.open()

    @cog_ext.cog_slash(name="bazaar")
    async def slash_bazaar(self, ctx):
        """Get Bazaar NPC stats."""
        await ctx.defer()
        await self.bazaar(ctx)

    @commands.command()
    async def auctions(self, ctx) -> None:
        """Get the first 30 auctions."""

        await ctx.channel.trigger_typing()
        data = await self.hypixel.auctions()
        menu = PaginatedMenu(ctx)
        split = list(divide_array(data.auctions, 9))
        auctionitems = split[:3]
        pagesend = []

        for auctionsloop in range(len(auctionitems)):
            pageauctions = Page(
                title=_("Current Auctions"),
                description=_(f"Page {auctionsloop + 1} of {(len(auctionitems))}"),
                color=self.bot.color,
            )
            pageauctions.set_author(
                name=_("Hypixel"), icon_url="https://hypixel.net/favicon-32x32.png"
            )
            pageauctions.set_thumbnail(
                url="https://hypixel.net/styles/hypixel-v2/images/header-logo.png"
            )
            for item in range(len(auctionitems[auctionsloop])):
                name = auctionitems[auctionsloop][item].item_name
                category = auctionitems[auctionsloop][item].category
                tier = auctionitems[auctionsloop][item].tier
                start_bid = auctionitems[auctionsloop][item].starting_bid
                won = auctionitems[auctionsloop][item].claimed
                highest_bid = auctionitems[auctionsloop][item].highest_bid_amount
                pageauctions.add_field(
                    name=_(name),
                    value=_(
                        f"Item Category: {category} \n Item Tier: {tier} \n Starting Bid: {start_bid} \n Item Won: {won} \n Highest Bid: {highest_bid}"
                    ),
                )
            pagesend.append(pageauctions)

        menu.add_pages(pagesend)

        await menu.open()

    @cog_ext.cog_slash(name="auctions")
    async def slash_auctions(self, ctx):
        """Get the first 30 auctions."""
        await ctx.defer()
        await self.auctions(ctx)

    @commands.command()
    async def guild(self, ctx: commands.Context, guildname: str) -> None:
        """Get's guild info by guild name."""
        await ctx.channel.trigger_typing()
        data = await self.hypixel.guild_by_name(guildname)

        embed = discord.Embed(
            title=_("Guild Info"),
            description=_(f"Guild info for {guildname}"),
            colour=self.bot.color,
        )
        embed.set_author(
            name=_("Hypixel"),
            url="https://hypixel.net/forums/skyblock.157/",
            icon_url="https://hypixel.net/favicon-32x32.png",
        )
        embed.set_thumbnail(
            url="https://hypixel.net/styles/hypixel-v2/images/header-logo.png"
        )
        embed.add_field(name=_("Guild Name: "), value=_(data.id))
        embed.add_field(name=_("Guild Name: "), value=_(data.name))
        embed.add_field(name=_("Guild Description: "), value=_(data.description))
        embed.add_field(name=_("Guild Tag: "), value=_(data.tag))
        embed.add_field(name=_("Guild Experience Points: "), value=_(data.exp))
        embed.add_field(name=_("Joinable: "), value=_(data.joinable))
        embed.add_field(name=_("Public: "), value=_(data.publicly_listed))

        await ctx.send(embed=embed)

    @cog_ext.cog_slash(name="guild")
    async def slash_auctions(self, ctx, guildname=None):
        """Get's guild info by guild name."""
        await ctx.defer()
        await self.guild(ctx, guildname)

    @commands.command()
    async def leaderboards(self, ctx: commands.Context) -> None:
        """Get current hypixel leaderboards"""
        await ctx.channel.trigger_typing()

        data = await self.hypixel.leaderboards()
        menu = PaginatedMenu(ctx)
        pagesend = []
        pagenumber = 1

        for i in data:
            if data[i]:
                pageleader = Page(
                    title=_(f"Current Hypixel Leaderboards for {data[i][0].title}"),
                    description=_(f"Page {pagenumber} of {len(data)}"),
                    color=self.bot.color,
                )
                pageleader.set_author(
                    name=_("Hypixel"), icon_url="https://hypixel.net/favicon-32x32.png"
                )
                pageleader.set_thumbnail(
                    url="https://hypixel.net/styles/hypixel-v2/images/header-logo.png"
                )
                leaderstring = ""

                for leader in range(len(data[i][0].leaders)):
                    player_data = await self.bot.mojang_player(
                        ctx.author, data[i][0].leaders[leader]
                    )
                    username = player_data["username"]
                    leaderstring += f"{username} \n"
                pageleader.add_field(
                    name=_(f"Top {len(data[i][0].leaders)} Leaderboard"),
                    value=_(leaderstring),
                )

                pagesend.append(pageleader)
                pagenumber += 1

        menu.add_pages(pagesend)
        menu.set_timeout(90)
        menu.allow_multisession()

        await menu.open()

    @cog_ext.cog_slash(name="leaderboards")
    async def slash_auctions(self, ctx):
        """Get's guild info by guild name."""
        await ctx.defer()
        await self.leaderboards(ctx)
