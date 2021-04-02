"""Images cog."""
import json
import logging
from datetime import datetime
from random import choice
from discord_slash.utils.manage_commands import create_option, create_choice

import discord
from discord.ext import commands
from obsidion.core.i18n import cog_i18n
from obsidion.core.i18n import Translator
from discord_slash import cog_ext


log = logging.getLogger(__name__)

_ = Translator("Fun", __file__)

minecraft = (
    "ᔑ",
    "ʖ",
    "ᓵ",
    "↸",
    "ᒷ",
    "⎓",
    "⊣",
    "⍑",
    "╎",
    "⋮",
    "ꖌ",
    "ꖎ",
    "ᒲ",
    "リ",
    "𝙹",
    "!",
    "¡",
    "ᑑ",
    "∷",
    "ᓭ",
    "ℸ",
    " ̣",
    "⚍",
    "⍊",
    "∴",
    " ̇",
    "|",
    "|",
    "⨅",
    "I",
    "II",
    "III",
    "IV",
    "V",
    "VI",
    "VII",
    "VIII",
    "IX",
    "X",
)
alphabet = "abcdefghijklmnopqrstuvwxyz123456789"


@cog_i18n(_)
class Fun(commands.Cog):
    def __init__(self, bot) -> None:
        """Init."""
        self.bot = bot

    @commands.command(aliases=["villagerspeak", "villagerspeech", "hmm"])
    async def villager(self, ctx, *, speech: str) -> None:
        """Hmm hm hmmm Hm hmmm hmm."""
        split = speech.split(" ")
        sentence = ""
        for _ in split:
            sentence += " " + choice(("hmm", "hm", "hmmm"))
        response = sentence.strip()
        await ctx.send(response)

    @cog_ext.cog_slash(name="villager", options=[
            create_option(
                name="text",
                description="Text to translate.",
                option_type=3,
                required=True,
            )
        ],)
    async def slash_villager(self, ctx, *, speech: str):
        await ctx.defer()
        await self.villager(ctx, speech)

    @commands.command()
    async def enchant(self, ctx, *, msg: str) -> None:
        """Enchant a message."""
        response = ""
        for letter in msg:
            if letter in alphabet:
                response += minecraft[alphabet.index(letter)]
            else:
                response += letter
        await ctx.send(f"{ctx.message.author.mention}, `{response}`")

    @cog_ext.cog_slash(
        name="enchant",
        options=[
            create_option(
                name="text",
                description="Text to enchant.",
                option_type=3,
                required=True,
            )
        ],
    )
    async def slash_enchant(self, ctx, *, msg: str):
        await ctx.defer()
        await self.enchant(ctx, msg)

    @commands.command()
    async def unenchant(self, ctx, *, msg: str) -> None:
        """Disenchant a message."""
        response = ""
        for letter in msg:
            if letter in minecraft:
                response += alphabet[minecraft.index(letter)]
            else:
                response += letter
        await ctx.send(f"{ctx.message.author.mention}, `{response}`")

    @cog_ext.cog_slash(
        name="unenchant",
        options=[
            create_option(
                name="text",
                description="Text to unenchant.",
                option_type=3,
                required=True,
            )
        ],
    )
    async def slash_unenchant(self, ctx, *, msg: str):
        """Disenchant a message."""
        await ctx.defer()
        await self.unenchant(ctx, msg)

    @commands.command()
    async def creeper(self, ctx) -> None:
        """Aw man."""
        await ctx.send("Aw man")

    @cog_ext.cog_slash(name="creeper")
    async def slash_creeper(self, ctx):
        """Aw man."""
        await ctx.defer()
        await self.creeper(ctx)

    @commands.command()
    async def rps(self, ctx, user_choice: str = None) -> None:
        """Play Rock Paper Shears."""
        options = ["rock", "paper", "shears"]
        if not user_choice or user_choice not in options:
            await ctx.send(
                _(
                    "That is an invalid option can you please choose from "
                    "rock, paper or shears"
                )
            )
            return
        c_choice = choice(options)
        if user_choice == options[options.index(user_choice) - 1]:
            await ctx.send(
                _("You chose {user_choice}, I chose {c_choice} I win.").format(
                    user_choice=user_choice, c_choice=c_choice
                )
            )
        elif c_choice == user_choice:
            await ctx.send(
                _(
                    "You chose {user_choice}, I chose {c_choice} looks like we have a tie."
                ).format(user_choice=user_choice, c_choice=c_choice)
            )
        else:
            await ctx.send(
                _("You chose {user_choice}, I chose {c_choice} you win.").format(
                    user_choice=user_choice, c_choice=c_choice
                )
            )

    @cog_ext.cog_slash(
        name="rps",
        options=[
            create_option(
                name="choice",
                description="Rock paper or shears",
                option_type=3,
                required=True,
                choices=[
                    create_choice(name="Rock", value="rock"),
                    create_choice(name="Paper", value="paper"),
                    create_choice(name="Shears", value="shears"),
                ],
            )
        ],
    )
    async def slash_rps(self, ctx, user_choice: str):
        """Play Rock Paper Shears"""
        await ctx.defer()
        await self.rps(ctx, user_choice)
