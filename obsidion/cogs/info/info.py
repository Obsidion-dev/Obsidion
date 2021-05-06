"""Info cog."""
import json
import logging
from datetime import datetime
from time import mktime
from typing import Any
from typing import Dict
from typing import Optional
from typing import Tuple
from typing import Union

import discord
import feedparser
import pytz
from discord.ext import commands
from discord_slash import cog_ext
from discord_slash import SlashContext
from discord_slash.utils.manage_commands import create_option
from obsidion.core import get_settings
from obsidion.core.i18n import cog_i18n
from obsidion.core.i18n import Translator


log = logging.getLogger(__name__)

_ = Translator("Info", __file__)


@cog_i18n(_)
class Info(commands.Cog):
    def __init__(self, bot) -> None:
        """Init."""
        self.bot = bot

    @commands.command(
        aliases=["whois", "p", "names", "namehistory", "pastnames", "namehis"]
    )
    async def profile(
        self, ctx: Union[commands.Context, SlashContext], username: Optional[str] = None
    ) -> None:
        """View a players Minecraft UUID, Username history and skin."""
        await ctx.channel.trigger_typing()
        profile_info = await self.bot.mojang_player(ctx.author, username)
        if username is None:
            username = profile_info["username"]
        uuid: str = profile_info["uuid"]
        names = profile_info["username_history"]
        h = 0
        for c in uuid.replace("-", ""):
            h = (31 * h + ord(c)) & 0xFFFFFFFF
        skin_type = "Alex"
        if (((h + 0x80000000) & 0xFFFFFFFF) - 0x80000000) % 2 == 0:
            skin_type = "Steve"

        name_list = ""
        for name in names[1:]:
            name_list += ("**{number}.** `{username}` - {date}\n").format(
                number=names.index(name) + 1,
                username=name["username"],
                date=(
                    datetime.strptime(name["changed_at"], "%Y-%m-%dT%H:%M:%S.000Z")
                ).strftime("%b %d, %Y"),
            )
        name_list += _("**1.** `{original}` - First Username").format(
            original=names[0]["username"]
        )

        embed = discord.Embed(
            title=_("Minecraft profile for {username}").format(username=username),
            color=self.bot.color,
        )

        embed.add_field(
            name="Account",
            inline=False,
            value=_("Full UUID: `{uuid}`\nShort UUID: `{short}`").format(
                uuid=uuid, short=uuid.replace("-", "")
            ),
        )
        embed.add_field(
            name="Textures",
            inline=True,
            value=_(
                "Skin: [Open Skin](https://visage.surgeplay.com/skin/512/"
                "{uuid})\nSkin Type: `{skin_type}`\nSkin History: [link]"
                "({skin_history})\nSlim: `{slim}`\nCustom: `{custom}`"
                "\nCape: `{cape}`"
            ).format(
                uuid=uuid,
                skin_type=skin_type,
                skin_history=f"https://mcskinhistory.com/player/{username}",
                slim=profile_info["textures"]["slim"]
                if "slim" in profile_info["textures"]
                else False,
                custom=profile_info["textures"]["custom"]
                if "custom" in profile_info["textures"]
                else False,
                cape=True if "cape" in profile_info["textures"] else False,
            ),
        )
        embed.add_field(
            name=_("Information"),
            inline=True,
            value=_(
                "Username Changes: `{changes}`\nNamemc: [link]({namemc})"
                "\nLegacy: `{legacy}`\nDemo: `{demo}`"
            ).format(
                changes=len(names) - 1,
                namemc=f"https://namemc.com/profile/{uuid}",
                legacy=profile_info["legacy"] if "legacy" in profile_info else False,
                demo=profile_info["demo"] if "demo" in profile_info else False,
            ),
        )
        embed.add_field(
            name=_("Name History"),
            inline=False,
            value=name_list,
        )
        embed.set_thumbnail(url=(f"https://visage.surgeplay.com/bust/{uuid}"))

        await ctx.send(embed=embed)

    @cog_ext.cog_slash(
        name="profile",
        options=[
            create_option(
                name="username",
                description="Username of player defaults to your linked username.",
                option_type=3,
                required=False,
            )
        ],
    )
    async def slash_profile(self, ctx: SlashContext, username: str = None) -> None:
        await ctx.defer()
        await self.profile(ctx, username)

    @staticmethod
    def get_server(ip: str, port: Optional[int] = None) -> Tuple[str, Optional[int]]:
        """Returns the server icon."""
        if ":" in ip:  # deal with them providing port in string instead of separate
            address, _port = ip.split(":")
            return (address, port)
        if port is not None:
            return (ip, port)
        return (ip, None)

    @commands.command(aliases=["servers", "s"])
    async def server(
        self,
        ctx: Union[commands.Context, SlashContext],
        address: Optional[str] = None,
        port: Optional[int] = None,
    ):
        """Minecraft server info."""
        await ctx.channel.trigger_typing()
        if address is None and ctx.guild is not None:
            address = await self.bot._guild_cache.get_server(ctx.guild)
        if address is None:
            await ctx.send(_("Please provide a server"))
            return
        if len(address.split(":")) > 2:
            await ctx.send(_("Please provide a valid address"))
            return
        server_ip, _port = self.get_server(address, port)
        port = _port if _port else port
        key = f"server_{server_ip}:{port}"
        if await self.bot.redis.exists(key):
            data = json.loads(await self.bot.redis.get(key))
        else:
            params: Dict[str, Union[str, int]] = (
                {"server": address}
                if port is None
                else {"server": address, "port": port}
            )
            async with self.bot.http_session.get(
                f"{get_settings().API_URL}/server/java", params=params
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                else:
                    data = None
            await self.bot.redis.set(key, json.dumps(data), expire=600)
        if data is None:
            await ctx.send(_("server could not be reached."))
            return
        embed = discord.Embed(
            title=_("Java Server: {server_ip}").format(server_ip=server_ip),
            color=self.bot.color,
        )
        embed.add_field(name=_("Description"), value=data["motd"]["clean"][0])

        embed.add_field(
            name="Players",
            value=_("Online: `{online}` \n " "Maximum: `{maximum}`").format(
                online=data["players"]["online"], maximum=data["players"]["max"]
            ),
        )
        embed.add_field(
            name=_("Version"),
            value=_(
                "Java Edition \n Running: `{version}` \n" "Protocol: `{protocol}`"
            ).format(version=data["version"], protocol=data["protocol"]),
            inline=False,
        )
        if data["icon"]:
            url = f"{get_settings().API_URL}/server/javaicon?server={server_ip}"
            if port is not None:
                url += f"&port={port}"
            embed.set_thumbnail(url=url)
        else:
            embed.set_thumbnail(
                url=(
                    "https://media.discordapp.net/attachments/493764139290984459"
                    "/602058959284863051/unknown.png"
                )
            )
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(
        name="server",
        options=[
            create_option(
                name="address",
                description="Address of server defaults to your linked server.",
                option_type=3,
                required=False,
            ),
            create_option(
                name="port",
                description="port of server defaults to that of your linked server.",
                option_type=3,
                required=False,
            ),
        ],
    )
    async def slash_server(
        self, ctx: SlashContext, address: str = None, port: int = None
    ) -> None:
        await ctx.defer()
        await self.server(ctx, address, port)

    @commands.command()
    async def serverpe(
        self,
        ctx: Union[commands.Context, SlashContext],
        address: str,
        port: Optional[int] = None,
    ) -> None:
        """Get information from a Minecraft Bedrock server."""
        await ctx.channel.trigger_typing()
        if len(address.split(":")) > 2:
            await ctx.send(_("Please provide a valid address"))
            return
        address, port = self.get_server(address, port)
        params: Dict[str, Union[str, int]] = (
            {"server": address} if port is None else {"server": address, "port": port}
        )
        async with self.bot.http_session.get(
            f"{get_settings().API_URL}/server/bedrock", params=params
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
            else:
                await ctx.send("Server could not be reached.")
                return
        embed = discord.Embed(
            title=_("Bedrock Server: {address}").format(address=address),
            color=self.bot.color,
        )
        embed.add_field(name=_("Description"), value="\n".join(data["motd"]))

        embed.add_field(
            name=_("Players"),
            value=_("Online: `{player_count}` \n " "Maximum: `{player_max}`").format(
                player_count=data["player_count"], player_max=data["player_max"]
            ),
        )
        embed.add_field(
            name=_("Version"),
            value=_(
                "Bedrock Edition \n Running: `{version}` \n" "Protocol: `{protocol}`"
            ).format(version=data["protocol_version"], protocol=data["protocol_name"]),
            inline=False,
        )
        embed.add_field(
            name=_("Info"),
            value=_("Gamemode: `{gamemode}` \n" "Latency: `{latency}`").format(
                version=data["gamemode"], protocol=data["latency"]
            ),
        )
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(
        name="serverpe",
        options=[
            create_option(
                name="address",
                description="Address of server defaults to your linked server.",
                option_type=3,
                required=True,
            ),
            create_option(
                name="port",
                description="port of server defaults to that of your linked server.",
                option_type=3,
                required=False,
            ),
        ],
    )
    async def slash_serverpe(
        self, ctx: SlashContext, address: str, port: int = None
    ) -> None:
        await ctx.defer()
        await self.serverpe(ctx, address, port)

    @commands.command(aliases=["sales"])
    async def status(self, ctx: Union[commands.Context, SlashContext]) -> None:
        """Check the status of all the Mojang services."""
        await ctx.channel.trigger_typing()
        async with self.bot.http_session.get(
            f"{get_settings().API_URL}/mojang/check"
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
            else:
                data = None
        sales_mapping = {
            "item_sold_minecraft": True,
            "prepaid_card_redeemed_minecraft": True,
            "item_sold_cobalt": False,
            "item_sold_scrolls": False,
        }
        payload = {"metricKeys": [k for (k, v) in sales_mapping.items() if v]}

        if await self.bot.redis.exists("status"):
            sales_data = json.loads(await self.bot.redis.get("status"))
        else:
            url = "https://api.mojang.com/orders/statistics"
            async with ctx.bot.http_session.post(url, json=payload) as resp:
                if resp.status == 200:
                    sales_data = await resp.json()
            await self.bot.redis.set("status", json.dumps(sales_data))

        services = ""
        for service in data:
            if data[service] == "green":
                services += _(
                    ":green_heart: - {service}: **This service is healthy.** \n"
                ).format(service=service)
            else:
                services += _(
                    ":heart: - {service}: **This service is offline.** \n"
                ).format(service=service)
        embed = discord.Embed(title=_("Minecraft Service Status"), color=0x00FF00)
        embed.add_field(
            name="Minecraft Game Sales",
            value=_("Total Sales: **{total}** Last 24 Hours: **{last}**").format(
                total=sales_data["total"], last=sales_data["last24h"]
            ),
        )
        embed.add_field(name=_("Minecraft Services:"), value=services, inline=False)

        await ctx.send(embed=embed)

    @cog_ext.cog_slash(name="status")
    async def slash_status(self, ctx: SlashContext) -> None:
        await ctx.defer()
        await self.status(ctx)

    @commands.command()
    async def wiki(
        self, ctx: Union[commands.Context, SlashContext], *, query: str
    ) -> None:
        """Get an article from the minecraft wiki."""
        await ctx.channel.trigger_typing()

        def generate_payload(query: str) -> dict:
            """Generate the payload for fandom based on a query string."""
            payload = {
                "action": "query",
                "titles": query.replace(" ", "_"),
                "format": "json",
                "formatversion": "2",  # Cleaner json results
                "prop": "extracts",  # Include extract in returned results
                "exintro": "1",  # Only return summary paragraph(s) before main content
                "redirects": "1",  # Follow redirects
                "explaintext": "1",  # Make sure it's plaintext (not HTML)
            }
            return payload

        base_url = "https://minecraft.fandom.com/api.php"
        footer_icon = (
            "https://upload.wikimedia.org/wikipedia/commons/thumb/5/53"
            "/Wikimedia-logo.png/600px-Wikimedia-logo.png"
        )

        payload = generate_payload(query)
        async with self.bot.http_session.get(base_url, params=payload) as resp:
            if resp.status == 200:
                result = await resp.json()
            else:
                result = None

        try:
            # Get the last page. Usually this is the only page.
            page = result["query"]["pages"][-1]
            title = page["title"]
            description = page["extract"].strip().replace("\n", "\n\n")
            url = f"https://minecraft.fandom.com/{title.replace(' ', '_')}"

            if len(description) > 1500:
                description = description[:1500].strip()
                description += f"... [(read more)]({url})"

            embed = discord.Embed(
                title=title,
                description=f"\u2063\n{description}\n\u2063",
                color=self.bot.color,
                url=url,
            )
            embed.set_footer(
                text=_("Information provided by Wikimedia"), icon_url=footer_icon
            )
            await ctx.send(embed=embed)

        except KeyError:
            await ctx.reply(
                _("I'm sorry, I couldn't find \"{query}\" on fandom").format(
                    query=query
                )
            )

    @cog_ext.cog_slash(
        name="wiki",
        options=[
            create_option(
                name="query",
                description="Thing to look up.",
                option_type=3,
                required=True,
            )
        ],
    )
    async def slash_wiki(self, ctx: SlashContext, query: str) -> None:
        await ctx.defer()
        await self.wiki(ctx, query)

    # @commands.command()
    async def mcbug(self, ctx: Union[commands.Context, SlashContext], bug: str) -> None:
        """Gets info on a bug from bugs.mojang.com."""
        await ctx.channel.trigger_typing()
        await ctx.send(f"https://bugs.mojang.com/rest/api/latest/issue/{bug}")
        async with self.bot.http_session.get(
            f"https://bugs.mojang.com/rest/api/latest/issue/{bug}"
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
            else:
                await ctx.reply(_("The bug {bug} was not found.").format(bug=bug))
                return
        embed = discord.Embed(
            description=data["fields"]["description"],
            color=self.bot.color,
        )

        embed.set_author(
            name=f"{data['fields']['project']['name']} - {data['fields']['summary']}",
            url=f"https://bugs.mojang.com/browse/{bug}",
        )

        info = _(
            "Version: {version}\n"
            "Reporter: {reporter}\n"
            "Created: {created}\n"
            "Votes: {votes}\n"
            "Updates: {updates}\n"
            "Watchers: {watched}"
        ).format(
            version=data["fields"]["project"]["name"],
            reporter=data["fields"]["creator"]["displayName"],
            created=data["fields"]["created"],
            votes=data["fields"]["votes"]["votes"],
            updates=data["fields"]["updated"],
            watched=data["fields"]["watches"]["watchCount"],
        )

        details = (
            f"Type: {data['fields']['issuetype']['name']}\n"
            f"Status: {data['fields']['status']['name']}\n"
        )
        if "name" in data["fields"]["resolution"]:
            details += _("Resolution: {resolution}\n").format(
                resolution=data["fields"]["resolution"]["name"]
            )
        if "version" in data["fields"]:
            details += (
                _("Affected: ")
                + f"{', '.join(s['name'] for s in data['fields']['versions'])}\n"
            )
        if "fixVersions" in data["fields"]:
            if len(data["fields"]["fixVersions"]) >= 1:
                details += (
                    _("Fixed Version: {fixed} + ").format(
                        fixed=data["fields"]["fixVersions"][0]
                    )
                    + f"{len(data['fields']['fixVersions'])}\n"
                )

        embed.add_field(name=_("Information"), value=info)
        embed.add_field(name=_("Details"), value=details)

        await ctx.send(embed=embed)

    @commands.command()
    async def version(
        self, ctx: Union[commands.Context, SlashContext], version: Optional[str] = None
    ) -> None:
        await ctx.channel.trigger_typing()
        async with self.bot.http_session.get(
            "https://launchermeta.mojang.com/mc/game/version_manifest.json"
        ) as resp:
            data = await resp.json()
        id2version = {}
        versions: Dict[str, Any] = {}

        for _version in reversed(data["versions"]):
            id2version[_version["id"]] = _version
            if _version["type"] == "release":
                version_num = ".".join(_version["id"].split(".")[:2])
                if version_num in versions:
                    _updated = versions[version_num]
                    _updated.append(_version)
                    versions[version_num] = _updated
                else:
                    versions[version_num] = [_version]
        embed = discord.Embed(
            colour=self.bot.color,
        )
        format = "%Y-%m-%dT%H:%M:%S%z"
        if version is not None:
            if version not in id2version:
                await ctx.send(_("Version is invalid."))
                return
            version_data = id2version[version]
            embed.set_author(
                name=_("Minecraft Java Edition {version}").format(version=version),
                url=f"https://minecraft.fandom.com/Java_Edition_{version}",
                icon_url=(
                    "https://www.minecraft.net/etc.clientlibs/minecraft"
                    "/clientlibs/main/resources/img/menu/menu-buy--reversed"
                    ".gif"
                ),
            )
            embed.add_field(
                name=version,
                value=_(
                    "Type: `{type}`\nRelease: `{released}`\nPackage URL: [link"
                    "]({package_url})\nMinecraft Wiki: [link]({wiki})"
                ).format(
                    type=version_data["type"],
                    released=datetime.strptime(version_data["releaseTime"], format),
                    package_url=version_data["url"],
                    wiki="https://minecraft.fandom.com/Java_Edition_{_version}",
                ),
            )
        else:
            embed.set_author(
                name=_("Minecraft Java Edition Versions"),
                icon_url=(
                    "https://www.minecraft.net/etc.clientlibs/minecraft"
                    "/clientlibs/main/resources/img/menu/menu-buy--reversed.gif"
                ),
            ),
            for _version in reversed(versions):
                embed.add_field(
                    name=_version,
                    value=_(
                        "Releases: `{releases}`\n"
                        "**Latest Version**\n"
                        "ID: `{id}`\n"
                        "Released: `{released}`\n"
                        "Wiki: [link]({link})"
                    ).format(
                        releases=len(versions[_version]),
                        id=versions[_version][-1]["id"],
                        released=datetime.strptime(
                            versions[_version][-1]["releaseTime"], format
                        ),
                        link=f"https://minecraft.fandom.com/Java_Edition_{_version}",
                    ),
                )
        await ctx.send(embed=embed)

    @commands.command()
    async def news(self, ctx: Union[commands.Context, SlashContext]) -> None:
        await ctx.channel.trigger_typing()
        async with self.bot.http_session.get(
            "https://www.minecraft.net/en-us/feeds/community-content/rss"
        ) as resp:
            text = await resp.text()
        data = feedparser.parse(text, "lxml")["entries"][:12]
        embed = discord.Embed(colour=self.bot.color)
        for post in data:
            format = "%d %m %Y"
            time = datetime.strftime(
                datetime.fromtimestamp(mktime(post["published_parsed"]), pytz.utc),
                format,
            )
            embed.add_field(
                name=post["title"],
                value=(
                    "Category: `{category}`\n"
                    "Published: `{pub}`\n"
                    "[Article Link]({link})"
                ).format(category=post["primarytag"], pub=time, link=post["id"]),
            )
        await ctx.send(embed=embed)
