"""Images cog."""
import json
import logging
from datetime import datetime
from time import mktime
from typing import Dict
from typing import Union

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
        self.mojang_service: Dict[str, str] = {}
        self.autopost.start()

    async def get_status(self) -> Union[discord.Embed, None]:
        async with self.bot.http_session.get(
            f"{get_settings().API_URL}/mojang/check"
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
            else:
                return None

        embed = discord.Embed(colour=self.bot.color)
        embed.set_author(name="Mojang service downtime")
        em = 0
        for service in data:
            if data[service] != "green" and service not in self.mojang_service:
                em = 1
                embed.add_field(name=_("Downtime"), value=service)
            elif data[service] == "green" and service in self.mojang_service:
                em = 1
                embed.add_field(name=_("Back Online"), value=service)
        if em == 0:
            return None
        return embed

    async def get_media(self) -> Union[discord.Embed, None]:
        """Get rss media."""
        async with self.bot.http_session.get(Minecraft_News_RSS) as resp:
            text = await resp.text()
        data = feedparser.parse(text, "lxml")

        # select the most recent post
        latest_post = data["entries"][0]

        # run checks to see wether it should be posted

        time = datetime.fromtimestamp(mktime(latest_post["published_parsed"]), pytz.utc)

        if time <= self.last_media_data:
            return None

        async with self.bot.http_session.get(latest_post["id"]) as resp:
            text = await resp.text()
        soup = BeautifulSoup(text, "lxml")
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
        self.last_media_data = time

        # create title
        embed.set_author(
            name=_("New Article on Minecraft.net"),
            url=latest_post["id"],
            icon_url=(
                "https://www.minecraft.net/etc.clientlibs/minecraft"
                "/clientlibs/main/resources/img/menu/menu-buy--reversed.gif"
            ),
        )

        return embed

    async def get_java_releases(self) -> Union[discord.Embed, None]:
        async with self.bot.http_session.get(
            "https://launchermeta.mojang.com/mc/game/version_manifest.json"
        ) as resp:
            data = await resp.json()
        last_release = data["versions"][0]

        format = "%Y-%m-%dT%H:%M:%S%z"
        time = datetime.strptime(last_release["time"], format)
        if time <= self.last_java_version_data:
            return None

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
                "[Minecraft Wiki](https://minecraft.fandom.com/Java_Edition_{id})"
            ).format(id=last_release["id"]),
        )

        embed.set_footer(text=_("Article Published"))
        embed.timestamp = time
        self.last_java_version_data = time
        # create title
        embed.set_author(
            name=_("New Minecraft Java Edition Snapshot"),
            url=f"https://minecraft.fandom.com/Java_Edition_{last_release['id']}",
            icon_url=(
                "https://www.minecraft.net/etc.clientlibs/minecraft"
                "/clientlibs/main/resources/img/menu/menu-buy--reversed.gif"
            ),
        )
        return embed

    @tasks.loop(minutes=10)
    async def autopost(self) -> None:
        posts = await self.bot.db.fetch("SELECT news FROM guild WHERE news IS NOT NULL")
        channels = {}
        for server in posts:
            n = json.loads(server["news"])
            for key in n.keys():
                if n[key] is not None:
                    if key in channels:

                        channels[key] = n[key]
                    else:
                        channels[key] = [n[key]]

        release_embed = await self.get_java_releases()
        article_embed = await self.get_media()
        status_embed = await self.get_status()
        if release_embed is not None and "release" in channels:
            # send embed
            for _channel in channels["release"]:
                channel = self.bot.get_channel(_channel)
                message = await channel.send(embed=release_embed)
                try:
                    await message.publish()
                except discord.errors.Forbidden:
                    pass
        if article_embed is not None and "article" in channels:
            for _channel in channels["article"]:
                channel = self.bot.get_channel(_channel)
                message = await channel.send(embed=article_embed)
                try:
                    await message.publish()
                except discord.errors.Forbidden:
                    pass

        if status_embed is not None and "status" in channels:
            for _channel in channels["status"]:
                channel = self.bot.get_channel(_channel)
                message = await channel.send(embed=status_embed)
                try:
                    await message.publish()
                except discord.errors.Forbidden:
                    pass

    def cog_unload(self) -> None:
        """Stop news posting tasks on cog unload."""
        self.autopost.cancel()
