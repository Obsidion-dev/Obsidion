"""Core Commands."""
import asyncio
import contextlib
import datetime
import inspect
import logging
import os
import sys
from typing import Optional

import discord
from babel import Locale as BabelLocale
from babel import UnknownLocaleError
from discord.ext import commands
from obsidion import __version__
from obsidion.core.i18n import cog_i18n
from obsidion.core.i18n import Translator

from . import i18n
from .utils.chat_formatting import box
from .utils.chat_formatting import humanize_timedelta
from .utils.chat_formatting import pagify
from .utils.predicates import MessagePredicate

log = logging.getLogger("obsidion")

_ = Translator("Core", __file__)


@cog_i18n(_)
class Core(commands.Cog):
    """Commands related to core functions."""

    def __init__(self, bot):
        """Init Core Commands."""
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
            await self.bot.wait_for("message", check=pred)
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
                "<https://github.com/Obsidion-dev/Obsidion/blob/master/LICENSE>"
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
        branch = "master"
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

    @commands.command(name="restart")
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

    @commands.command()
    @commands.has_guild_permissions(manage_nicknames=True)
    @commands.guild_only()
    async def nickname(self, ctx: commands.Context, *, nickname: str = None):
        """Sets Obsidion's nickname."""
        try:
            if nickname and len(nickname) > 32:
                await ctx.send(
                    _("Failed to change nickname. Must be 32 characters or fewer.")
                )
                return
            await ctx.guild.me.edit(nick=nickname)
        except discord.Forbidden:
            await ctx.send(_("I lack the permissions to change my own nickname."))
        else:
            await ctx.send(_("Done."))

    @commands.command(aliases=["serverprefixes"])
    @commands.bot_has_guild_permissions(manage_guild=True)
    @commands.guild_only()
    async def prefix(self, ctx: commands.Context, _prefix: Optional[str]):
        """Sets Obsidion's server prefix(es)."""
        if not _prefix:
            await ctx.bot.set_prefixes(guild=ctx.guild)
            await ctx.send(_("Guild prefixes have been reset."))
            return
        await ctx.bot.set_prefixes(guild=ctx.guild, prefix=_prefix)
        await ctx.send(_("Prefix set."))

    @commands.command()
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def locale(self, ctx: commands.Context, language_code: str):
        """
        Changes the bot's locale in this server.

        `<language_code>` can be any language code with country code included,
        e.g. `en-US`, `de-DE`, `fr-FR`, `pl-PL`, etc.


        Use "default" to return to the bot's default set language.
        To reset to English, use "en-US".
        """
        if language_code.lower() == "default":
            global_locale = await self.bot._config.locale()
            i18n.set_contextual_locale(global_locale)
            await self.bot._i18n_cache.set_locale(ctx.guild, None)
            await ctx.send(_("Locale has been set to the default."))
            return
        try:
            locale = BabelLocale.parse(language_code, sep="-")
        except (ValueError, UnknownLocaleError):
            await ctx.send(_("Invalid language code. Use format: `en-US`"))
            return
        if locale.territory is None:
            await ctx.send(
                _(
                    "Invalid format - language code has to "
                    "include country code, e.g. `en-US`"
                )
            )
            return
        standardized_locale_name = f"{locale.language}-{locale.territory}"
        i18n.set_contextual_locale(standardized_locale_name)
        await self.bot._i18n_cache.set_locale(ctx.guild, standardized_locale_name)
        await ctx.send(_("Locale has been set."))

    @commands.command(aliases=["region"])
    @commands.has_guild_permissions(manage_guild=True)
    async def regionalformat(self, ctx: commands.Context, language_code: str = None):
        """
        Changes bot's regional format in this server. This
        is used for formatting date, time and numbers.

        `<language_code>` can be any language code with country code included,
        e.g. `en-US`, `de-DE`, `fr-FR`, `pl-PL`, etc.

        Leave `<language_code>` empty to base regional formatting on
        bot's locale in this server.
        """
        if language_code is None:
            i18n.set_contextual_regional_format(None)
            await self.bot._i18n_cache.set_regional_format(ctx.guild, None)
            await ctx.send(
                _(
                    "Regional formatting will now be based "
                    "on bot's locale in this server."
                )
            )
            return

        try:
            locale = BabelLocale.parse(language_code, sep="-")
        except (ValueError, UnknownLocaleError):
            await ctx.send(_("Invalid language code. Use format: `en-US`"))
            return
        if locale.territory is None:
            await ctx.send(
                _(
                    "Invalid format - language code has to "
                    "include country code, e.g. `en-US`"
                )
            )
            return
        standardized_locale_name = f"{locale.language}-{locale.territory}"
        i18n.set_contextual_regional_format(standardized_locale_name)
        await self.bot._i18n_cache.set_regional_format(
            ctx.guild, standardized_locale_name
        )
        await ctx.send(
            _(
                "Regional formatting will now be based on `{language_code}` locale."
            ).format(language_code=standardized_locale_name)
        )
