"""Images cog."""
import logging
import json
from time import mktime

import discord
from discord.ext import commands
from discord.ext import tasks
import bs4

import feedparser

from obsidion.core.i18n import cog_i18n
from obsidion.core.i18n import Translator
from obsidion.core import get_settings
from datetime import datetime

log = logging.getLogger(__name__)

_ = Translator("News", __file__)

Minecraft_News_RSS = "https://www.minecraft.net/en-us/feeds/community-content/rss"
Categories = ("Minecraft Builds", "News", "Deep Dives", "Guides")

@cog_i18n(_)
class News(commands.Cog):
    def __init__(self, bot) -> None:
        """Init."""
        self.bot = bot
        self.last_media_data = datetime.now()
        self.last_java_version_data = datetime.now()
        self.get_media.start()
        self.get_java_releases.start()

    @tasks.loop(minutes=10)
    async def get_media(self) -> None:
        """Get rss media."""
        async with self.bot.http_session.get(Minecraft_News_RSS) as resp:
            text = await resp.text()
        data = feedparser.parse(text)

        # select the most recent post
        latest_post = data["entries"][0]
        print(latest_post)

        # run checks to see wether it should be posted

        time = datetime.fromtimestamp(mktime(latest_post["published_parsed"]))

        if time <= self.last_data:
            return
        # create discord embed
        description = f"Summary: {latest_post['summary']}"

        embed = discord.Embed(
            title=latest_post["title_detail"]["value"]
            .replace("--", ": ")
            .replace("-", " ")
            .upper(),
            description=description,
            colour=0x00FF00,
            url=latest_post["id"],
        )

        # add categories
        embed.set_image(url=f"https://minecraft.net{latest_post['imageurl']}")
        embed.add_field(name="Category", value=latest_post["primarytag"])
        embed.add_field(name="Publish Date", value=" ".join(latest_post["published"].split(" ")[:4]))

        # author info
        # embed.set_thumbnail =
        # embed.add_field(name="Author:", value)

        # create footer
        embed.set_footer(text="Article Published")
        embed.timestamp = time
        self.last_data = time

        # create title
        embed.set_author(
            name="New Article on Minecraft.net",
            url=f"https://minecraft.net{latest_post['imageurl']}",
            icon_url=(
                "https://www.minecraft.net/etc.clientlibs/minecraft"
                "/clientlibs/main/resources/img/menu/menu-buy--reversed.gif"
            ),
        )

        # send embed
        channel = self.bot.get_channel(725790318938685520)
        message = await channel.send(embed=embed)
        try:
            await message.publish()
        finally:
            pass

    @tasks.loop(minutes=10)
    async def get_java_releases(self) -> None:
        async with self.bot.http_session.get("https://launchermeta.mojang.com/mc/game/version_manifest.json") as resp:
            data = await resp.json()
        last_release = data["versions"][0]

        format = '%Y-%m-%dT%H:%M:%S%z'
        time = datetime.strptime(last_release["time"], format)
        if time <= self.last_data or last_release["type"] != "snapshot":
            return

        embed = discord.Embed(
            colour=0x00FF00,
        )

        embed.add_field(name="Name", value=last_release["id"])
        embed.add_field(name="Package URL", value=f"[Package URL]({last_release['url']})")
        embed.add_field(name="Minecraft Wiki", value=f"[Minecraft Wiki](https://minecraft.gamepedia.com/Java_Edition_{last_release['id']})")

        embed.set_footer(text="Article Published")
        embed.timestamp = time
        self.last_data = time
        # create title
        embed.set_author(
            name="New Minecraft Java Edition Snapshot",
            url=f"https://minecraft.gamepedia.com/Java_Edition_{last_release['id']}",
            icon_url=(
                "https://www.minecraft.net/etc.clientlibs/minecraft"
                "/clientlibs/main/resources/img/menu/menu-buy--reversed.gif"
            ),
        )
        # send embed
        channel = self.bot.get_channel(725790318938685520)
        message = await channel.send(embed=embed)
        try:
            await message.publish()
        finally:
            pass

    @commands.command(hidden=True)
    @commands.is_owner()
    async def java_releases(self, ctx) -> None:
        async with self.bot.http_session.get("https://launchermeta.mojang.com/mc/game/version_manifest.json") as resp:
            data = await resp.json()
        last_release = data["versions"][0]
        format = '%Y-%m-%dT%H:%M:%S%z'
        time = datetime.strptime(last_release["time"], format)
        # if time <= self.last_data or last_release["type"] != "snapshot":
        #     return

        embed = discord.Embed(
            colour=0x00FF00,
        )

        embed.add_field(name="Name", value=last_release["id"])
        embed.add_field(name="Package URL", value=f"[Package URL]({last_release['url']})")
        embed.add_field(name="Minecraft Wiki", value=f"[Minecraft Wiki](https://minecraft.gamepedia.com/Java_Edition_{last_release['id']})")

        embed.set_footer(text="Article Published")
        embed.timestamp = time
        self.last_data = time
        # create title
        embed.set_author(
            name="New Minecraft Java Edition Snapshot",
            url=f"https://minecraft.gamepedia.com/Java_Edition_{last_release['id']}",
            icon_url=(
                "https://www.minecraft.net/etc.clientlibs/minecraft"
                "/clientlibs/main/resources/img/menu/menu-buy--reversed.gif"
            ),
        )
        # send embed
        await ctx.send(embed=embed)
        

    @commands.command(hidden=True)
    @commands.is_owner()
    async def get_latest_news(self, ctx) -> None:
        """Get rss media."""
        async with self.bot.http_session.get(Minecraft_News_RSS) as resp:
            text = await resp.text()
        data = feedparser.parse(text)

        # select the most recent post
        latest_post = data["entries"][0]
#
        time = datetime.fromtimestamp(mktime(latest_post["published_parsed"]))
        description = f"Summary: {latest_post['summary']}"

        embed = discord.Embed(
            title=latest_post["title_detail"]["value"]
            .replace("--", ": ")
            .replace("-", " ")
            .upper(),
            description=description,
            colour=0x00FF00,
            url=latest_post["id"],
        )

        # add categories
        embed.set_image(url=f"https://minecraft.net{latest_post['imageurl']}")
        embed.add_field(name="Category", value=latest_post["primarytag"])
        embed.add_field(name="Publish Date", value=" ".join(latest_post["published"].split(" ")[:4]))

        # create footer
        embed.set_footer(text="Article Published")
        embed.timestamp = time

        # create title
        embed.set_author(
            name="New Article on Minecraft.net",
            url=f"https://minecraft.net{latest_post['imageurl']}",
            icon_url=(
                "https://www.minecraft.net/etc.clientlibs/minecraft"
                "/clientlibs/main/resources/img/menu/menu-buy--reversed.gif"
            ),
        )

        # send embed
        await ctx.send(embed=embed)
        await ctx.send(self.last_data)

    def cog_unload(self) -> None:
        """Stop news posting tasks on cog unload."""
        self.get_media.cancel()
        self.get_java_releases.cancel()

    