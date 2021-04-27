"""Core Commands."""
import asyncio
import contextlib
import datetime
import inspect
import logging
import os
import sys
from typing import List, Optional
from typing import Union

import discord
from discord.ext import commands
from discord.ext.commands.core import Command, Group, wrap_callback
from discord.ext.commands.errors import CommandError
from discord_slash import cog_ext
from discord_slash import SlashContext
from obsidion import __version__
from obsidion.core.i18n import cog_i18n
from obsidion.core.i18n import Translator
from obsidion.core.utils.predicates import MessagePredicate

from .utils.chat_formatting import box
from .utils.chat_formatting import humanize_timedelta
from .utils.chat_formatting import pagify


log = logging.getLogger("obsidion")

_ = Translator("Core", __file__)


@cog_i18n(_)
class Core(commands.Cog):
    """Commands related to core functions."""

    def __init__(self, bot) -> None:
        """Init Core Commands."""
        self.bot = bot

    @commands.command()
    async def ping(self, ctx: Union[commands.Context, SlashContext]) -> None:
        """Pong."""
        await ctx.send(_("Pong! ({latency}ms)").format(latency=self.bot.latency * 1000))

    @cog_ext.cog_slash(name="ping", description="View bot latency.")
    async def slash_ping(self, ctx: SlashContext) -> None:
        """View bot latency."""
        await ctx.defer()
        await self.ping(ctx)

    @commands.command()
    async def info(self, ctx: Union[commands.Context, SlashContext]) -> None:
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
        embed.add_field(name=("About Obsidion"), value=about, inline=False)

        embed.set_footer(
            text=_(
                "Bringing joy since the 2nd of April 2020 (over {} days ago!)"
            ).format(days_since)
        )
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(name="info", description="View info about Obsidion.")
    async def slash_info(self, ctx: SlashContext) -> None:
        """Shows info about Obsidion."""
        await ctx.defer()
        await self.info(ctx)

    @commands.command()
    async def uptime(self, ctx: Union[commands.Context, SlashContext]) -> None:
        """Shows Obsidion's uptime."""
        since = ctx.bot.uptime.strftime("%Y-%m-%d %H:%M:%S")
        delta = datetime.datetime.utcnow() - self.bot.uptime
        uptime_str = humanize_timedelta(timedelta=delta) or _("Less than one second")
        await ctx.send(
            _("Been up for: **{time_quantity}** (since {timestamp} UTC)").format(
                time_quantity=uptime_str, timestamp=since
            )
        )

    @cog_ext.cog_slash(name="uptime", description="View Obsidion's uptime.")
    async def slash_uptime(self, ctx: SlashContext) -> None:
        """Shows Obsidion's uptime."""
        await ctx.defer()
        await self.uptime(ctx)

    @commands.command()
    async def invite(self, ctx: Union[commands.Context, SlashContext]) -> None:
        """Invite the bot to your server."""
        embed = discord.Embed(
            description=_(
                "You can invite {name} to your Discord server by"
                " [clicking here]({invite})."
            ).format(name=self.bot.user.name, invite=self.bot._invite),
            color=self.bot.color,
        )

        await ctx.send(embed=embed)

    @cog_ext.cog_slash(name="invite", description="Invite the bot to your server.")
    async def slash_invite(self, ctx: SlashContext) -> None:
        """Invite the bot to your server."""
        await ctx.defer()
        await self.invite(ctx)

    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def leave(self, ctx: commands.Context) -> None:
        """Leaves the current server."""
        await ctx.send(
            _("Are you sure you want me to leave the current server? (yes/no)").format(
                ctx.guild.name
            )
        )
        await self.leave_server(ctx, ctx.guild)

    @commands.command()
    @commands.is_owner()
    async def leave_servers(self, ctx: commands.Context) -> None:
        """Lists and allows Obsidion to leave servers."""
        guilds: List[discord.Guild] = sorted(self.bot.guilds, key=lambda s: s.name.lower())
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
            if not isinstance(pred.result, int):
                return
            guild = guilds[pred.result]
            await ctx.send(
                _("Are you sure you want me to leave {}? (yes/no)").format(guild.name)
            )
            await self.leave_server(ctx, guild)

    async def leave_server(self, ctx: commands.Context, guild: discord.Guild) -> None:
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
    async def license_info_command(
        self, ctx: Union[commands.Context, SlashContext]
    ) -> None:
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

    @cog_ext.cog_slash(name="licenseinfo", description="Invite the bot to your server.")
    async def slash_licenseinfo(self, ctx: SlashContext) -> None:
        """Leaves the current server."""
        await ctx.defer()
        await self.license_info_command(ctx)

    @commands.command()
    async def source(
        self,
        ctx: Union[commands.Context, SlashContext],
        *,
        command: Optional[str] = None,
    ) -> None:
        """Displays my full source code or for a specific command.

        To display the source code of a subcommand you can separate it by
        periods, e.g. account.link for the link subcommand of the account command
        or by spaces.
        """  # noqa: DAR101, DAR201
        source_url = "https://github.com/Obsidion-dev/Obsidion"
        branch = "main"
        if command is None:
            await ctx.send(source_url)
            return
        filename: str
        if command == "help":
            src = type(self.bot.help_command)
            module = src.__module__
            filename = str(inspect.getsourcefile(src))
        else:
            obj = self.bot.get_command(command.replace(".", " "))
            if obj is None:
                await ctx.send("Could not find command.")
                return

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

    @cog_ext.cog_slash(
        name="source",
        description="Displays my full source code or for a specific command.",
    )
    async def slash_source(self, ctx: SlashContext, source: str = None) -> None:
        """Displays my full source code or for a specific command."""
        await ctx.defer()
        await self.source(ctx, source)

    @commands.command(name="shutdown")
    @commands.is_owner()
    async def _shutdown(self, ctx: commands.Context, silently: bool = False) -> None:
        """Shuts down the bot."""
        wave = "\N{WAVING HAND SIGN}"
        skin = "\N{EMOJI MODIFIER FITZPATRICK TYPE-3}"
        with contextlib.suppress(discord.HTTPException):
            if not silently:
                await ctx.send("Shutting down... " + wave + skin)
        await ctx.bot.shutdown()

    @commands.command(name="restart", aliases=["reboot"])
    @commands.is_owner()
    async def _restart(self, ctx: commands.Context, silently: bool = False) -> None:
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
    async def traceback(self, ctx: commands.Context, public: bool = False) -> None:
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

    @cog_ext.cog_slash(name="help")
    async def slash_help(self, ctx: SlashContext, command=None) -> None:
        await ctx.defer()
        bot = self.bot
        cmd = bot.help_command

        cmd = cmd.copy()
        cmd.context = ctx
        if command == None:
            await cmd.prepare_help_command(ctx, None)
            mapping = cmd.get_bot_mapping()
            injected = wrap_callback(cmd.send_bot_help)
            try:
                return await injected(mapping)
            except CommandError as e:
                await cmd.on_help_command_error(ctx, e)
                return None
        entity = command
        if entity is None:
            return None
        if isinstance(entity, str):
            entity = bot.get_cog(entity) or bot.get_command(entity)
        try:
            entity.qualified_name
        except AttributeError:
            # if we're here then it's not a cog, group, or command.
            return None
        await cmd.prepare_help_command(ctx, entity.qualified_name)
        try:
            if hasattr(entity, "__cog_commands__"):
                injected = wrap_callback(cmd.send_cog_help)
                return await injected(entity)
            elif isinstance(entity, Group):
                injected = wrap_callback(cmd.send_group_help)
                return await injected(entity)
            elif isinstance(entity, Command):
                injected = wrap_callback(cmd.send_command_help)
                return await injected(entity)
            else:
                return None
        except CommandError as e:
            await cmd.on_help_command_error(self, e)
