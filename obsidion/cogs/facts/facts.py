"""Images cog."""
import logging
from typing import Union, Optional

import discord
from discord.ext import commands
from obsidion.core import get_settings
from obsidion.core.i18n import cog_i18n
from obsidion.core.i18n import Translator
from discord_slash import cog_ext, SlashContext
from discord_slash.utils.manage_commands import create_option

log = logging.getLogger(__name__)

_ = Translator("Facts", __file__)


@cog_i18n(_)
class Facts(commands.Cog):
    def __init__(self, bot) -> None:
        """Init."""
        self.bot = bot

    @commands.command()
    async def block(self, ctx: Union[SlashContext, commands.Context], name: str, version: Optional[str] = "1.16.5") -> None:
        params = (
                {"name_id": name,"version": version}
            )
        async with self.bot.http_session.get(
            f"{get_settings().API_URL}/info/block", params=params
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
            else:
                await ctx.send("Could not find block")
                return
        embed = discord.Embed(colour=self.bot.color)
        embed.set_author(
                name=data["displayName"],
                url=f"https://minecraft.fandom.com/{name}")
        embed.add_field(name=_("Display Name"), value=data["displayName"])
        embed.add_field(name=_("ID"), value=data["id"])
        embed.add_field(name=_("Stack Size"), value=data["stackSize"])
        embed.add_field(name=_("hardness"), value=data["hardness"])
        embed.add_field(name=_("diggable"), value=data["diggable"])
        embed.add_field(name=_("transparent"), value=data["transparent"])
        embed.add_field(name=_("filterLight"), value=data["filterLight"])
        embed.add_field(name=_("emitLight"), value=data["emitLight"])
        embed.add_field(name=_("material"), value=data["material"])
        embed.add_field(name=_("resistance"), value=data["resistance"])
        embed.add_field(name=_("harvestTools"), value="\n".join(data["harvestTools"]))
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(
        name="block",
        options=[
            create_option(
                name="name",
                description="Name of block.",
                option_type=3,
                required=True,
            ),
            create_option(
                name="version",
                description="Minecraft version.",
                option_type=3,
                required=False,
            ),
        ],
    )
    async def slash_block(self, ctx: SlashContext, name: str, version: str = "1.16.5") -> None:
        await ctx.defer()
        await self.block(ctx, name, version)


    @commands.command()
    async def entity(self, ctx: Union[SlashContext, commands.Context], name: str,  version: Optional[str] = "1.16.5") -> None:
        params = (
                {"name": name,"version": version}
            )
        async with self.bot.http_session.get(
            f"{get_settings().API_URL}/info/entity", params=params
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
            else:
                await ctx.send("Could not find entity")
                return
        embed = discord.Embed(colour=self.bot.color)
        embed.set_author(
                name=data["displayName"],
                url=f"https://minecraft.fandom.com/{name}")
        embed.add_field(name=_("Display Name"), value=data["displayName"])
        embed.add_field(name=_("ID"), value=data["id"])
        embed.add_field(name=_("width"), value=data["width"])
        embed.add_field(name=_("height"), value=data["height"])
        embed.add_field(name=_("type"), value=data["type"])
        embed.add_field(name=_("category"), value=data["category"])
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(
        name="entity",
        options=[
            create_option(
                name="name",
                description="Name of entity.",
                option_type=3,
                required=True,
            ),
            create_option(
                name="version",
                description="Minecraft version.",
                option_type=3,
                required=False,
            ),
        ],
    )
    async def slash_entity(self, ctx: SlashContext, name: str, version: str = "1.16.5") -> None:
        await ctx.defer()
        await self.entity(ctx, name, version)

    @commands.command()
    async def biome(self, ctx: Union[SlashContext, commands.Context], name: str, version: Optional[str] = "1.16.5") -> None:
        params = (
                {"name": name,"version": version}
            )
        async with self.bot.http_session.get(
            f"{get_settings().API_URL}/info/biome", params=params
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
            else:
                await ctx.send("Could not find biome")
                return
        def getRGBfromI(RGBint):
            blue =  RGBint & 255
            green = (RGBint >> 8) & 255
            red =   (RGBint >> 16) & 255
            return red, green, blue
        colour = getRGBfromI(data["color"])
        embed = discord.Embed(colour=discord.Colour.from_rgb(colour[0], colour[1], colour[2]))
        embed.set_author(
                name=data["displayName"],
                url=f"https://minecraft.fandom.com/{name}")
        embed.add_field(name=_("Display Name"), value=data["displayName"])
        embed.add_field(name=_("Category"), value=data["category"])
        embed.add_field(name=_("Dimension"), value=data["dimension"])
        embed.add_field(name=_("ID"), value=data["id"])
        embed.add_field(name=_("Temperature"), value=data["temperature"])
        embed.add_field(name=_("Colour"), value="#%02x%02x%02x" % tuple(colour))
        embed.add_field(name=_("Rainfall"), value=data["rainfall"])
        embed.add_field(name=_("Precipitation"), value=data["precipitation"])
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(
        name="biome",
        options=[
            create_option(
                name="name",
                description="Name of biome.",
                option_type=3,
                required=True,
            ),
            create_option(
                name="version",
                description="Minecraft version.",
                option_type=3,
                required=False,
            ),
        ],
    )
    async def slash_biome(self, ctx: SlashContext, name: str, version: str = "1.16.5") -> None:
        await ctx.defer()
        await self.biome(ctx, name, version)

    @commands.command()
    async def effect(self, ctx: Union[SlashContext, commands.Context], name: str, version: Optional[str] = "1.16.5") -> None:
        params = (
                {"name": name.capitalize(),"version": version}
            )
        async with self.bot.http_session.get(
            f"{get_settings().API_URL}/info/effect", params=params
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
            else:
                await ctx.send("Could not find biome")
                return
    
        embed = discord.Embed(colour=self.bot.color)
        embed.set_author(
                name=data["displayName"],
                url=f"https://minecraft.fandom.com/{name}")
        embed.add_field(name=_("Display Name"), value=data["displayName"])
        embed.add_field(name=_("ID"), value=data["id"])
        embed.add_field(name=_("type"), value=data["type"])
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(
        name="effect",
        options=[
            create_option(
                name="name",
                description="Name of effect.",
                option_type=3,
                required=True,
            ),
            create_option(
                name="version",
                description="Minecraft version.",
                option_type=3,
                required=False,
            ),
        ],
    )
    async def slash_effect(self, ctx: SlashContext, name: str, version: str = "1.16.5") -> None:
        await ctx.defer()
        await self.effect(ctx, name, version)

