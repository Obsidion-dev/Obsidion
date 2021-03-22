"""Images cog."""
import json
import logging
from datetime import datetime
from time import mktime

import discord
import feedparser
import pytz
from bs4 import BeautifulSoup
from discord.ext import commands
from discord.ext import tasks
from obsidion.core import get_settings
from obsidion.core.i18n import cog_i18n
from obsidion.core.i18n import Translator

log = logging.getLogger(__name__)

_ = Translator("News", __file__)

Minecraft_News_RSS = "https://www.minecraft.net/en-us/feeds/community-content/rss"


@cog_i18n(_)
class News(commands.Cog):
    def __init__(self, bot) -> None:
        """Init."""
        self.bot = bot
        self.last_media_data = datetime.now(pytz.utc)
        self.last_java_version_data = datetime.now(pytz.utc)
        self.get_media.start()
        self.get_java_releases.start()

    @tasks.loop(minutes=10)
    async def get_media(self) -> None:
        """Get rss media."""
        async with self.bot.http_session.get(Minecraft_News_RSS) as resp:
            text = await resp.text()
        data = feedparser.parse(text, "lxml")

        # select the most recent post
        latest_post = data["entries"][0]

        # run checks to see wether it should be posted

        time = datetime.fromtimestamp(mktime(latest_post["published_parsed"]), pytz.utc)

        if time <= self.last_media_data:
            return

        async with self.bot.http_session.get(latest_post["id"]) as resp:
            text = await resp.text()
        soup = BeautifulSoup(text)
        author_image = f"https://www.minecraft.net{soup.find('img', id='author-avatar').get('src')}"
        author = soup.find("dl", class_="attribution__details").dd.string
        text = soup.find("div", class_="end-with-block").p.text

        embed = discord.Embed(
            title=soup.find("h1").string,
            description=text,
            colour=self.bot.color,
            url=f"https://minecraft.net{latest_post['imageurl']}",
            thumbnail=author_image,
        )

        # add categories
        embed.set_image(url=f"https://minecraft.net{latest_post['imageurl']}")
        embed.set_thumbnail(url=author_image)
        embed.add_field(name=_("Category"), value=latest_post["primarytag"])
        embed.add_field(name=_("Author"), value=author)
        embed.add_field(
            name=_("Publish Date"),
            value=" ".join(latest_post["published"].split(" ")[:4]),
        )

        # create footer
        embed.set_footer(text=_("Article Published"))
        embed.timestamp = time
        # self.last_media_data = time

        # create title
        embed.set_author(
            name=_("New Article on Minecraft.net"),
            url=latest_post["id"],
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
        async with self.bot.http_session.get(
            "https://launchermeta.mojang.com/mc/game/version_manifest.json"
        ) as resp:
            data = await resp.json()
        last_release = data["versions"][0]

        format = "%Y-%m-%dT%H:%M:%S%z"
        time = datetime.strptime(last_release["time"], format)
        if time <= self.last_java_version_data or last_release["type"] != "snapshot":
            return

        embed = discord.Embed(
            colour=self.bot.color,
        )

        embed.add_field(name=_("Name"), value=last_release["id"])
        embed.add_field(
            name=_("Package URL"),
            value=_("[Package URL]({url})").format(url=last_release["url"]),
        )
        embed.add_field(
            name=_("Minecraft Wiki"),
            value=_(
                "[Minecraft Wiki](https://minecraft.gamepedia.com/Java_Edition_{id})"
            ).format(id=last_release["id"]),
        )

        embed.set_footer(text=_("Article Published"))
        embed.timestamp = time
        self.last_java_version_data = time
        # create title
        embed.set_author(
            name=_("New Minecraft Java Edition Snapshot"),
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

    def cog_unload(self) -> None:
        """Stop news posting tasks on cog unload."""
        self.get_media.cancel()
        self.get_java_releases.cancel()
