"""Fun cog."""
import logging
from random import choice
from typing import List
import re

from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.utils.manage_commands import create_choice
from discord_slash.utils.manage_commands import create_option
from obsidion.core.i18n import cog_i18n
from obsidion.core.i18n import Translator


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
    "!¡",
    "ᑑ",
    "∷",
    "ᓭ",
    "ℸ",
    "⚍",
    "⍊",
    "∴",
    " ̇",
    "||",
    "⨅",
)
alphabet = "abcdefghijklmnopqrstuvwxyz"


@cog_i18n(_)
class Fun(commands.Cog):
    def __init__(self, bot) -> None:
        """Init."""
        self.bot = bot
        self.pvp_mes = self.load_from_file("pvp")
        self.kill_mes = self.load_from_file("kill")
        self.build_ideas_mes = self.load_from_file("build_ideas")

    @staticmethod
    def load_from_file(file: str) -> List[str]:
        """Load text from file.
        Args:
            file (str): file name
        Returns:
            List[str]: list of input
        """
        with open(f"obsidion/cogs/fun/resources/{file}.txt") as f:
            content = f.readlines()
        return [x.strip() for x in content]

    @commands.command(aliases=["idea", "bidea"])
    async def buildidea(self, ctx) -> None:
        """Get an idea for a new idea."""
        await ctx.send(
            _("Here is something cool to build: {b_idea}.").format(
                b_idea=choice(self.build_ideas_mes)
            )
        )

    @commands.command(aliases=["slay"])
    async def kill(self, ctx, member) -> None:
        """Kill that pesky friend in a fun and stylish way."""
        await ctx.send(choice(self.kill_mes).replace("member", member))

    @commands.command(aliases=["battle"])
    async def pvp(
        self,
        ctx,
        member1,
        member2=None,
    ) -> None:
        """Duel someone."""
        if not member2:
            member2 = ctx.message.author.mention

        await ctx.send(
            choice(self.pvp_mes).replace("member1", member1).replace("member2", member2)
        )

    @commands.command(aliases=["villagerspeak", "villagerspeech", "hmm"])
    async def villager(self, ctx, *, speech: str) -> None:
        """Hmm hm hmmm Hm hmmm hmm."""
        last_was_alpha = False  # Used to detect the start of a word
        last_was_h = False  # Used to prevent 'H's without 'm's
        last_was_lower_m = False  # Used to make "HmmHmm" instead of "HmmMmm"
        sentence = ""

        for char in speech:

            if char.isalpha():  # Alphabetical letter -- Replace with 'Hmm'

                if not last_was_alpha:  # First letter of alphabetical string
                    sentence += "H" if char.isupper() else "h"
                    last_was_h = True
                    last_was_lower_m = False

                else:  # Non-first letter
                    if not char.isupper():
                        sentence += "m"
                        last_was_lower_m = True
                        last_was_h = False
                    else:
                        # Use an 'H' instead to allow CamelCase 'HmmHmm's
                        if last_was_lower_m:
                            sentence += "H"
                            last_was_h = True
                        else:
                            sentence += "M"
                            last_was_h = False
                        last_was_lower_m = False

                last_was_alpha = True  # Remember for next potential 'M'

            else:  # Non-alphabetical letters -- Do not replace
                # Add an m after 'H's without 'm's
                if last_was_h:
                    sentence += "m"
                    last_was_h = False
                # Add non-letter character without changing it
                sentence += char
                last_was_alpha = False

        # If the laster character is an H, add a final 'm'
        if last_was_h:
            sentence += "m"

        # Done
        await ctx.send(sentence)

    @cog_ext.cog_slash(
        name="villager",
        options=[
            create_option(
                name="text",
                description="Text to translate.",
                option_type=3,
                required=True,
            )
        ],
    )
    async def slash_villager(self, ctx, *, speech: str):
        await ctx.defer()
        await self.villager(ctx, speech)

    @commands.command()
    async def enchant(self, ctx, *, msg: str) -> None:
        """Enchant a message."""
        response = ""
        letter_pos = 0
        while letter_pos < len(msg):
            letter = msg[letter_pos:letter_pos+2] if msg[letter_pos:letter_pos+2] in minecraft else msg[letter_pos]
            if letter in alphabet:
                response += minecraft[alphabet.index(letter)]
            elif letter in minecraft:
                response += alphabet[minecraft.index(letter)]
                if len(letter) == 2:
                    letter_pos += 1
            else:
                response += letter
            letter_pos += 1
        await ctx.send(response)


    @cog_ext.cog_slash(
        name="enchant",
        options=[
            create_option(
                name="text",
                description="Text to enchant or unenchant.",
                option_type=3,
                required=True,
            )
        ],
    )
    async def slash_enchant(self, ctx, *, msg: str):
        await ctx.defer()
        await self.enchant(ctx, msg)

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
                    "You chose {user_choice}, I chose {c_choice} looks like we"
                    " have a tie."
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
