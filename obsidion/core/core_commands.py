"""Core Commands."""
import asyncio
import contextlib
import datetime
import inspect
import logging
from obsidion.core.utils.predicates import MessagePredicate
import os
import sys

import discord
from discord.ext import commands
from obsidion import __version__
from obsidion.core.i18n import cog_i18n
from obsidion.core.i18n import Translator

from . import i18n
from .utils.chat_formatting import box
from .utils.chat_formatting import humanize_timedelta
from .utils.chat_formatting import pagify

log = logging.getLogger("obsidion")

_ = Translator("Core", __file__)


@cog_i18n(_)
class Core(commands.Cog):
    """Commands related to core functions."""

    def __init__(self, bot):
        """Init Core Commands."""
        self.bot = bot

    @commands.command()
    async def ping(self, ctx: commands.Context):
        """Pong."""
        await ctx.send("Pong.")

    @commands.command()
    async def info(self, ctx: commands.Context):
        """Shows info about Obsidion."""
        author_repo = "https://github.com/Darkflame72"
        org_repo = "https://github.com/Obsidion-dev"
        obsidion_repo = org_repo + "/Obsidion"
        support_server_url = "https://discord.gg/fWxtKFVmaW"
        dpy_repo = "https://github.com/Rapptz/discord.py"
        python_url = "https://www.python.org/"
        since = datetime.datetime(2020, 4, 2)
        days_since = (datetime.datetime.utcnow() - since).days

        app_info = await self.bot.application_info()
        if app_info.team:
            owner = app_info.team.name
        else:
            owner = app_info.owner

        dpy_version = "[{}]({})".format(discord.__version__, dpy_repo)
        python_version = "[{}.{}.{}]({})".format(*sys.version_info[:3], python_url)
        obsidion_version = "[{}]({})".format(__version__, obsidion_repo)

        about = _(
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
            text=_("Bringing joy since 23rd March 2020 (over {} days ago!)").format(
                days_since
            )
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def uptime(self, ctx: commands.Context):
        """Shows Obsidion's uptime."""
        since = ctx.bot.uptime.strftime("%Y-%m-%d %H:%M:%S")
        delta = datetime.datetime.utcnow() - self.bot.uptime
        uptime_str = humanize_timedelta(timedelta=delta) or _("Less than one second")
        await ctx.send(
            _("Been up for: **{time_quantity}** (since {timestamp} UTC)").format(
                time_quantity=uptime_str, timestamp=since
            )
        )

    @commands.command()
    async def invite(self, ctx: commands.Context) -> None:
        """Invite the bot to your server."""
        embed = discord.Embed(
            description=_(
                "You can invite {name} to your Discord server by"
                " [clicking here]({invite})."
            ).format(name=self.bot.user.name, invite=self.bot._invite),
            color=self.bot.color,
        )

        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def leave(self, ctx: commands.Context):
        """Leaves the current server."""
        await ctx.send(
            _("Are you sure you want me to leave the current server? (yes/no)").format(
                ctx.guild.name
            )
        )
        await self.leave_server(ctx, ctx.guild)

    @commands.command()
    @commands.is_owner()
    async def servers(self, ctx: commands.Context):
        """Lists and allows Obsidion to leave servers."""
        guilds = sorted(self.bot.guilds, key=lambda s: s.name.lower())
        msg = ""
        responses = []
        for i, server in enumerate(guilds, 1):
            msg += "{}: {} (`{}`)\n".format(i, server.name, server.id)
            responses.append(str(i))

        for page in pagify(msg, ["\n"]):
            await ctx.send(page)

        query = await ctx.send(_("To leave a server, just type its number."))

        pred = MessagePredicate.contained_in(responses, ctx)
        try:
            await self.bot.wait_for("message", check=pred, timeout=15)
        except asyncio.TimeoutError:
            try:
                await query.delete()
            except discord.errors.NotFound:
                pass
        else:
            guild = guilds[pred.result]
            await ctx.send(
                _("Are you sure you want me to leave {}? (yes/no)").format(guild.name)
            )
            await self.leave_server(ctx, guild)

    async def leave_server(self, ctx, guild):
        pred = MessagePredicate.yes_or_no(ctx)
        try:
            await self.bot.wait_for("message", check=pred, timeout=15.0)
        except asyncio.TimeoutError:
            await ctx.send(_("Response timed out."))
            return
        else:
            if pred.result is True:
                await ctx.send(_("Alright. Bye :wave:"))
                log.debug(_("Leaving guild '{}'").format(guild.name))
                await guild.leave()
            else:
                await ctx.send(_("Alright, I'll stay then. :)"))

    # Removing this command from forks is a violation of the
    # AGPLv3 under which it is licensed.
    # Otherwise interfering with the ability for this command
    # to be accessible is also a violation.
    @commands.command(name="licenseinfo", aliases=["license"])
    async def license_info_command(self, ctx: commands.Context):
        """
        Get info about Obsidion's licenses.
        """

        embed = discord.Embed(
            description=_(
                "This bot is an instance of the Obsidion Discord Bot.\n"
                "Obsidion is an open source application made available "
                "to the public and "
                "licensed under the GNU AGPL v3. The full text of this "
                "license is available to you at "
                "<https://github.com/Obsidion-dev/Obsidion/blob/main/LICENSE>"
            ),
            color=self.bot.color,
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
        branch = "main"
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
            branch = "main"

        final_url = (
            f"<{source_url}/blob/{branch}/{location}#L{firstlineno}"
            f"-L{firstlineno + len(lines) - 1}>"
        )
        await ctx.send(final_url)

    @commands.command(name="shutdown")
    @commands.is_owner()
    async def _shutdown(self, ctx: commands.Context, silently: bool = False):
        """Shuts down the bot."""
        wave = "\N{WAVING HAND SIGN}"
        skin = "\N{EMOJI MODIFIER FITZPATRICK TYPE-3}"
        with contextlib.suppress(discord.HTTPException):
            if not silently:
                await ctx.send("Shutting down... " + wave + skin)
        await ctx.bot.shutdown()

    @commands.command(name="restart", aliases=["reboot"])
    @commands.is_owner()
    async def _restart(self, ctx: commands.Context, silently: bool = False):
        """Attempts to restart Obsidion.

        Makes Obsidion quit with exit code 26.
        The restart is not guaranteed: it must be dealt
        with by the process manager in use."""
        with contextlib.suppress(discord.HTTPException):
            if not silently:
                await ctx.send("Restarting...")
        await ctx.bot.shutdown(restart=True)

    @commands.command()
    @commands.is_owner()
    async def traceback(self, ctx: commands.Context, public: bool = False):
        """Sends to the owner the last command exception that has occurred.

        If public (yes is specified), it will be sent to the chat instead."""
        if not public:
            destination = ctx.author
        else:
            destination = ctx.channel

        if self.bot._last_exception:
            for page in pagify(self.bot._last_exception, shorten_by=10):
                try:
                    await destination.send(box(page, lang="py"))
                except discord.HTTPException:
                    await ctx.channel.send(
                        _(
                            "I couldn't send the traceback message to you in DM. "
                            "Either you blocked me or you disabled DMs in this server."
                        )
                    )
                    return
        else:
            await ctx.send(_("No exception has occurred yet."))
