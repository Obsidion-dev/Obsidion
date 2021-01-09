import datetime
import sys
import asyncio
import contextlib
import logging
import inspect
import os


import discord
from obsidion import __version__
from .utils.chat_formatting import (
    box,
    humanize_timedelta,
    pagify,
)
from .utils.predicates import MessagePredicate


from discord.ext import commands

log = logging.getLogger("obsidion")


class Core(commands.Cog):
    """Commands related to core functions."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    async def ping(self, ctx: commands.Context):
        """Pong."""
        await ctx.send("Pong.")

    @commands.command()
    async def info(self, ctx: commands.Context):
        """Shows info about Obsidion."""
        author_repo = "https://github.com/Darkflame72"
        org_repo = "https://github.com/Obsidion-dev"
        obsidion_repo = org_repo + "/Obsidion"
        support_server_url = "https://discord.gg/rnAtymZnzH"
        dpy_repo = "https://github.com/Rapptz/discord.py"
        python_url = "https://www.python.org/"
        since = datetime.datetime(2020, 3, 23)
        days_since = (datetime.datetime.utcnow() - since).days

        app_info = await self.bot.application_info()
        if app_info.team:
            owner = app_info.team.name
        else:
            owner = app_info.owner

        dpy_version = "[{}]({})".format(discord.__version__, dpy_repo)
        python_version = "[{}.{}.{}]({})".format(*sys.version_info[:3], python_url)
        obsidion_version = "[{}]({})".format(__version__, obsidion_repo)

        about = (
            "This bot is an instance of [Obsidion, an open source Discord bot]({}) "
            "created by [Darkflame72]({}) and [improved by many]({}).\n\n"
            "Obsidion is backed by a passionate community who contributes and "
            "creates content for everyone to enjoy. [Join us today]({}) "
            "and help us improve!\n\n"
            "(c) Obsidion-dev"
        ).format(obsidion_repo, author_repo, org_repo, support_server_url)

        embed = discord.Embed(color=self.bot.color)
        embed.add_field(name=("Instance owned by"), value=str(owner))
        embed.add_field(name="Python", value=python_version)
        embed.add_field(name="discord.py", value=dpy_version)
        embed.add_field(name=("Obsidion version"), value=obsidion_version)
        embed.add_field(name=("Docker hub image"), value=obsidion_version)
        embed.add_field(name=("About Obsidion"), value=about, inline=False)

        embed.set_footer(
            text=("Bringing joy since 23rd March 2020 (over {} days ago!)").format(
                days_since
            )
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def uptime(self, ctx: commands.Context):
        """Shows Obsidion's uptime."""
        since = ctx.bot.uptime.strftime("%Y-%m-%d %H:%M:%S")
        delta = datetime.datetime.utcnow() - self.bot.uptime
        uptime_str = humanize_timedelta(timedelta=delta) or ("Less than one second")
        await ctx.send(
            ("Been up for: **{time_quantity}** (since {timestamp} UTC)").format(
                time_quantity=uptime_str, timestamp=since
            )
        )

    @commands.command()
    async def invite(self, ctx: commands.Context) -> None:
        """Invite the bot to your server."""
        perms = discord.Permissions()
        perms.add_reactions = True
        perms.send_messages = True
        perms.read_messages = True
        perms.use_external_emojis = True
        url = discord.utils.oauth_url(
            self.bot.user.id,
            permissions=perms,
            redirect_uri="https://discord.obsidion-dev.com",
        )
        embed = discord.Embed(
            description=(
                f"You can invite {self.bot.user.name} to your Discord server by"
                f" [clicking here]({url})."
            ),
            color=self.bot.color,
        )

        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def leave(self, ctx: commands.Context):
        """Leaves the current server."""
        await ctx.send(("Are you sure you want me to leave this server? (y/n)"))

        pred = MessagePredicate.yes_or_no(ctx)
        try:
            await self.bot.wait_for("message", check=pred)
        except asyncio.TimeoutError:
            await ctx.send(("Response timed out."))
            return
        else:
            if pred.result is True:
                await ctx.send(("Alright. Bye :wave:"))
                log.debug(("Leaving guild '{}'").format(ctx.guild.name))
                await ctx.guild.leave()
            else:
                await ctx.send(("Alright, I'll stay then. :)"))

    @commands.command()
    @commands.is_owner()
    async def servers(self, ctx: commands.Context):
        """Lists and allows [botname] to leave servers."""
        guilds = sorted(list(self.bot.guilds), key=lambda s: s.name.lower())
        msg = ""
        responses = []
        for i, server in enumerate(guilds, 1):
            msg += "{}: {} (`{}`)\n".format(i, server.name, server.id)
            responses.append(str(i))

        for page in pagify(msg, ["\n"]):
            await ctx.send(page)

        query = await ctx.send(("To leave a server, just type its number."))

        pred = MessagePredicate.contained_in(responses, ctx)
        try:
            await self.bot.wait_for("message", check=pred, timeout=15)
        except asyncio.TimeoutError:
            try:
                await query.delete()
            except discord.errors.NotFound:
                pass
        else:
            await self.leave_confirmation(guilds[pred.result], ctx)

    async def leave_confirmation(self, guild, ctx):
        if guild.owner.id == ctx.bot.user.id:
            await ctx.send(("I cannot leave a guild I am the owner of."))
            return

        await ctx.send(
            ("Are you sure you want me to leave {}? (yes/no)").format(guild.name)
        )
        pred = MessagePredicate.yes_or_no(ctx)
        try:
            await self.bot.wait_for("message", check=pred, timeout=15)
            if pred.result is True:
                await guild.leave()
                if guild != ctx.guild:
                    await ctx.send(("Done."))
            else:
                await ctx.send(("Alright then."))
        except asyncio.TimeoutError:
            await ctx.send(("Response timed out."))

    # Removing this command from forks is a violation of the AGPLv3 under which it is licensed.
    # Otherwise interfering with the ability for this command to be accessible is also a violation.
    @commands.command(
        name="licenseinfo",
    )
    async def license_info_command(self, ctx: commands.Context):
        """
        Get info about Obsidion's licenses.
        """

        embed = discord.Embed(
            description=(
                "This bot is an instance of the Obsidion Discord Bot.\n"
                "Obsidion is an open source application made available "
                "to the public and "
                "licensed under the GNU AGPL v3. The full text of this "
                "license is available to you at "
                "<https://github.com/Obsidion-dev/Obsidion/blob/master/LICENSE>"
            ),
            color=self.bot.color
        )

        await ctx.send(embed=embed)

    @commands.command()
    async def source(self, ctx: commands.Context, *, command: str = None) -> None:
        """Displays my full source code or for a specific command.

        To display the source code of a subcommand you can separate it by
        periods, e.g. account.link for the link subcommand of the account command
        or by spaces.
        """  # noqa: DAR101, DAR201
        source_url = "https://github.com/Obsidion-dev/Obsidion"
        branch = "V0.4"
        if command is None:
            return await ctx.send(source_url)

        if command == "help":
            src = type(self.bot.help_command)
            module = src.__module__
            filename = inspect.getsourcefile(src)
        else:
            obj = self.bot.get_command(command.replace(".", " "))
            if obj is None:
                return await ctx.send("Could not find command.")

            # since we found the command we're looking for, presumably anyway, let's
            # try to access the code itself
            src = obj.callback.__code__
            module = obj.callback.__module__
            filename = src.co_filename

        lines, firstlineno = inspect.getsourcelines(src)
        if not module.startswith("discord"):
            # not a built-in command
            location = os.path.relpath(filename).replace("\\", "/")
        else:
            location = module.replace(".", "/") + ".py"
            source_url = "https://github.com/Rapptz/discord.py"
            branch = "master"

        final_url = (
            f"<{source_url}/blob/{branch}/{location}#L{firstlineno}"
            f"-L{firstlineno + len(lines) - 1}>"
        )
        await ctx.send(final_url)
