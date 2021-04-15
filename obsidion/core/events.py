import logging
import traceback
from datetime import datetime

import discord
from discord.ext import commands
from obsidion.core.config import PlayerNotExist, get_settings
from obsidion.core.i18n import cog_i18n
from obsidion.core.i18n import Translator

from .i18n import set_contextual_locales_from_guild
from .utils.chat_formatting import box, format_perms_list, pagify
from .utils.chat_formatting import humanize_timedelta
from .utils.chat_formatting import inline


log = logging.getLogger("obsidion")

_ = Translator("Events", __file__)


@cog_i18n(_)
class Events(commands.Cog):
    """Important bot events."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener("on_connect")
    async def on_connect(self):
        if self.bot.uptime is None:
            log.info("Connected to Discord. Getting ready...")
            perms = discord.Permissions()
            perms.add_reactions = True
            perms.send_messages = True
            perms.read_messages = True
            perms.embed_links = True
            url = discord.utils.oauth_url(
                self.bot.user.id,
                permissions=perms,
                redirect_uri="https://discord.obsidion-dev.com",
                scopes=("bot", "applications.commands"),
            )
            self.bot._invite = url

    @commands.Cog.listener()
    async def on_message(self, message):
        await set_contextual_locales_from_guild(self.bot, message.guild)

    @commands.Cog.listener("on_ready")
    async def on_ready(self):
        if self.bot.uptime is not None:
            return

        self.bot.uptime = datetime.utcnow()

    @commands.Cog.listener("on_slash_command_error")
    async def _on_slash_command_error(self, ctx, ex) -> None:
        print(ex)
        # print(ex.original)
        await self.handle_check_failure(ctx, ex)

    @staticmethod
    async def handle_check_failure(ctx: commands.Context, e) -> None:
        """
        Send an error message in `ctx` for certain types of CheckFailure.
        The following types are handled:
        * BotMissingPermissions
        * BotMissingRole
        * BotMissingAnyRole
        * NoPrivateMessage
        * InWhitelistCheckFailure
        """
        bot_missing_errors = (
            commands.errors.MissingPermissions,
            commands.errors.MissingRole,
            commands.errors.MissingAnyRole,
        )

        if isinstance(e, bot_missing_errors):
            missing = [
                perm.replace("_", " ").replace("guild", "server").title()
                for perm in e.missing_perms
            ]
            if len(missing) > 2:
                fmt = f"{'**, **'.join(missing[:-1])}, and {missing[-1]}"
            else:
                fmt = " and ".join(missing)
            if len(missing) > 1:
                await ctx.send(
                    _("Sorry, it looks like you don't have the **{fmt}** permissions I need to do that.").format(fmt=fmt)
                )
            else:
                await ctx.send(
                    _("Sorry, it looks like you don't have the **{fmt}** permission I need to do that.").format(fmt=fmt)
                )

    @commands.Cog.listener("on_command_error")
    async def on_command_error(self, ctx, error, unhandled_by_cog=False):
        if not unhandled_by_cog:
            if hasattr(ctx.command, "on_error"):
                return

            if ctx.cog:
                if (
                    commands.Cog._get_overridden_method(ctx.cog.cog_command_error)
                    is not None
                ):
                    return

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send_help(ctx.command)
        elif isinstance(error, commands.ArgumentParsingError):
            msg = _("`{user_input}` is not a valid value for `{command}`").format(
                user_input=error.user_input, command=error.cmd
            )
            if error.custom_help_msg:
                msg += f"\n{error.custom_help_msg}"
            await ctx.send(msg)
            if error.send_cmd_help:
                await ctx.send_help(ctx.command)
        elif isinstance(error, commands.ConversionError):
            if error.args:
                await ctx.send(error.args[0])
            else:
                await ctx.send_help(ctx.command)
        elif isinstance(error, commands.UserInputError):
            await ctx.send_help(ctx.command)
        elif isinstance(error, commands.BotMissingPermissions):
            if bin(error.missing.value).count("1") == 1:  # Only one perm missing
                msg = _(
                    "I require the {permission} permission to execute that command."
                ).format(permission=format_perms_list(error.missing))
            else:
                msg = _(
                    "I require {permission_list} permissions to execute that command."
                ).format(permission_list=format_perms_list(error.missing))
            await ctx.send(msg)
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send(("That command is not available in DMs."))
        elif isinstance(error, commands.PrivateMessageOnly):
            await ctx.send(("That command is only available in DMs."))
        elif isinstance(error, commands.CheckFailure):
            await self.handle_check_failure(ctx, error)
        elif isinstance(error, commands.CommandOnCooldown):
            if self.bot._bypass_cooldowns and ctx.author.id in self.bot.owner_ids:
                ctx.command.reset_cooldown(ctx)
                new_ctx = await self.bot.get_context(ctx.message)
                await self.bot.invoke(new_ctx)
                return
            if delay := humanize_timedelta(seconds=error.retry_after):
                msg = _("This command is on cooldown. Try again in {delay}.").format(
                    delay=delay
                )
            else:
                msg = _("This command is on cooldown. Try again in 1 second.")
            await ctx.send(msg, delete_after=error.retry_after)
        elif isinstance(error, commands.MaxConcurrencyReached):
            if error.per is commands.BucketType.default:
                if error.number > 1:
                    msg = _(
                        "Too many people using this command."
                        " It can only be used {number} times concurrently."
                    ).format(number=error.number)
                else:
                    msg = _(
                        "Too many people using this command."
                        " It can only be used once concurrently."
                    )
            elif error.per in (commands.BucketType.user, commands.BucketType.member):
                if error.number > 1:
                    msg = _(
                        "That command is still completing,"
                        " it can only be used {number} times per {type} concurrently."
                    ).format(number=error.number, type=error.per.name)
                else:
                    msg = _(
                        "That command is still completing,"
                        " it can only be used once per {type} concurrently."
                    ).format(type=error.per.name)
            else:
                if error.number > 1:
                    msg = _(
                        "Too many people using this command."
                        " It can only be used {number} times per {type} concurrently."
                    ).format(number=error.number, type=error.per.name)
                else:
                    msg = _(
                        "Too many people using this command."
                        " It can only be used once per {type} concurrently."
                    ).format(type=error.per.name)
            await ctx.send(msg)
        elif isinstance(error, commands.CommandInvokeError):
            if isinstance(error.original, discord.errors.HTTPException):
                if error.original.code == 50035:
                    await ctx.send("Invalid input, too long.")
                    return
            elif isinstance(error.original, PlayerNotExist):
                await ctx.reply(
                    _(
                        "The user does not exist, please check wether the username is correct."
                    ).format(author=ctx.message.author.mention)
                )
                return
            log.exception(
                "Exception in command '{}'".format(ctx.command.qualified_name),
                exc_info=error.original,
            )

            message = _(
                "Error in command '{command}'. It has "
                "been recorded and should be fixed soon."
            ).format(command=ctx.command.qualified_name)
            exception_log = "Exception in command '{}'\n" "".format(
                ctx.command.qualified_name
            )
            exception_log += "".join(
                traceback.format_exception(type(error), error, error.__traceback__)
            )
            self.bot._last_exception = exception_log
            await ctx.send(inline(message))
            destination = self.bot.get_channel(get_settings().STACK_TRACE_CHANNEL)
            embed = discord.Embed(title="Bug", colour=0x00FF00)

            embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)
            embed.add_field(name="Command", value=ctx.command)
            embed.timestamp = ctx.message.created_at

            if ctx.guild is not None:
                embed.add_field(
                    name="Server",
                    value=f"{ctx.guild.name} (ID: {ctx.guild.id})",
                    inline=False,
                )

            embed.add_field(
                name="Channel",
                value=f"{ctx.channel} (ID: {ctx.channel.id})",
                inline=False,
            )
            embed.set_footer(text=f"Author ID: {ctx.author.id}")

            await destination.send(embed=embed)
            for page in pagify(self.bot._last_exception, shorten_by=10):
                try:
                    await destination.send(box(page, lang="py"))
                except discord.HTTPException:
                    log.warning(
                        "Could not send traceback to traceback channel use /traceback to get the most recent error"
                    )
                    return
        else:
            log.exception(type(error).__name__, exc_info=error)
