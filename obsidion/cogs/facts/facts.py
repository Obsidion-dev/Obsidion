"""Images cog."""
import logging
from typing import Union

import discord
from asyncpixel import Hypixel as _Hypixel
from discord.ext import commands
from obsidion.core import get_settings
from obsidion.core.i18n import cog_i18n
from obsidion.core.i18n import Translator

log = logging.getLogger(__name__)

_ = Translator("Facts", __file__)


@cog_i18n(_)
class Facts(commands.Cog):
    def __init__(self, bot) -> None:
        """Init."""
        self.bot = bot

    @commands.command()
    async def block(self, ctx, id: Union[str, int]):
        pass

    @commands.command()
    async def item(self, ctx, id: Union[str, int]):
        pass

    @commands.command()
    async def mob(self, ctx, id: Union[str, int]):
        pass

    @commands.command()
    async def structure(self, ctx, id: Union[str, int]):
        pass

    @commands.command()
    async def biome(self, ctx, id: Union[str, int]):
        pass

    @commands.command()
    async def update(self, ctx, id: Union[str, int]):
        pass

    @commands.command()
    async def trivia(self, ctx, id: Union[str, int]):
        pass

    @commands.command()
    async def fact(self, ctx, id: Union[str, int]):
        pass

    @commands.command()
    async def effect(self, ctx, id: Union[str, int]):
        pass

    @commands.command()
    async def advancement(self, ctx, id: Union[str, int]):
        pass

    @commands.command()
    async def potion(self, ctx, id: Union[str, int]):
        pass

    @commands.command()
    async def image(self, ctx, id: Union[str, int]):
        pass

    @commands.command()
    async def gamemode(self, ctx, id: Union[str, int]):
        pass

    @commands.command()
    async def difficulty(self, ctx, id: Union[str, int]):
        pass
