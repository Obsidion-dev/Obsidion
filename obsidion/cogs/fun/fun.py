import logging
from random import choice

from discord.ext import commands

minecraft = [
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
]
alphabet = "abcdefghijklmnopqrstuvwxyz123456789"

log = logging.getLogger(__name__)


def load_from_file(file):
    """load a file"""
    with open(f"obsidion/cogs/fun/resources/{file}.txt") as f:
        content = f.readlines()
    return [x.strip() for x in content]


class fun(commands.Cog):
    """commands that are bot related"""

    def __init__(self, bot):
        self.bot = bot
        self.pvp_mes = load_from_file("pvp")
        self.kill_mes = load_from_file("kill")
        self.build_ideas_mes = load_from_file("build_ideas")

    @commands.command(aliases=["villagerspeak", "villagerspeech", "hmm"])
    @commands.cooldown(rate=1, per=1.0, type=commands.BucketType.user)
    async def villager(self, ctx: commands.Context, *, speech: str):
        """Convert english to Villager speech hmm."""
        last_was_alpha = False
        sentence = ""
        for char in speech:
            if char.isalpha():
                if not last_was_alpha:
                    if char.isupper(): sentence += "H"
                    else: sentence += "h"
                else:
                    if char.isupper(): sentence += "M"
                    else: sentence += "m"
                last_was_alpha = True
            else:
                sentence += char
                last_was_alpha = False
        response = sentence.strip()
        await ctx.send(f"{ctx.message.author.mention}, `{response}`")

    @commands.command()
    @commands.cooldown(rate=1, per=1.0, type=commands.BucketType.user)
    async def enchant(self, ctx: commands.Context, *, msg: str):
        """Enchant a message"""
        response = ""
        for letter in msg:
            if letter in alphabet:
                response += minecraft[alphabet.index(letter)]
            else:
                response += letter
        await ctx.send(f"{ctx.message.author.mention}, `{response}`")

    @commands.command()
    @commands.cooldown(rate=1, per=1.0, type=commands.BucketType.user)
    async def unenchant(self, ctx: commands.Context, *, msg: str):
        """Disenchant a message"""
        response = ""
        for letter in msg:
            if letter in minecraft:
                response += alphabet[minecraft.index(letter)]
            else:
                response += letter
        await ctx.send(f"{ctx.message.author.mention}, `{response}`")

    @commands.command()
    @commands.cooldown(rate=1, per=1.0, type=commands.BucketType.user)
    async def creeper(self, ctx):
        """Aw man"""
        await ctx.send("Aw man")

    @commands.command(aliases=["idea", "bidea"])
    @commands.cooldown(rate=1, per=1.0, type=commands.BucketType.user)
    async def buildidea(self, ctx: commands.Context):
        """Get an idea for a new idea"""
        # await ctx.send(self.build_ideas)
        await ctx.send(
            f"Here is something cool to build: {choice(self.build_ideas_mes)}."
        )

    @commands.command(aliases=["slay"])
    @commands.cooldown(rate=1, per=1.0, type=commands.BucketType.user)
    async def kill(self, ctx, member=None):
        """Kill that pesky friend in a fun and stylish way"""
        if (
            not member
            or str(member) == f"<@{self.bot.owner_id}>"
            or str(member) == f"<@!{self.bot.owner_id}>"
            or str(member) == "<@691589447074054224>"
            or str(member) == "<@!691589447074054224>"
        ):
            # this included some protection for the owners and the bot itself
            await ctx.send("Good Try!")
            member = ctx.message.author.mention

        await ctx.send(choice(self.kill_mes).replace("member", member))

    @commands.command(aliases=["battle"])
    @commands.cooldown(rate=1, per=1.0, type=commands.BucketType.user)
    async def pvp(self, ctx, member1=None, member2=None):
        """Duel someone"""
        if member1:
            if not member2:
                member2 = ctx.message.author.mention

            await ctx.send(
                choice(self.pvp_mes)
                .replace("member1", member1)
                .replace("member2", member2)
            )
        else:
            await ctx.send("Please provide 2 people to fight")

    @commands.command()
    @commands.cooldown(rate=1, per=1.0, type=commands.BucketType.user)
    async def rps(self, ctx, user_choice=None):
        """play Rock Paper Shears"""
        options = ["rock", "paper", "shears"]
        if user_choice and user_choice in options:
            c_choice = choice(options)
            if user_choice == options[options.index(user_choice) - 1]:
                await ctx.send(f"You chose {user_choice}, I chose {c_choice} I win.")
            elif c_choice == user_choice:
                await ctx.send(
                    f"You chose {user_choice}, I chose {c_choice} looks like we have a tie."
                )
            else:
                await ctx.send(f"You chose {user_choice}, I chose {c_choice} you win.")
        else:
            await ctx.send(
                "That is an invalid option can you please choose from rock, paper or shears"
            )
