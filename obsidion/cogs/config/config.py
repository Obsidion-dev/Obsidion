"""Images cog."""
import asyncio
import logging
from typing import Optional

import discord
from babel import Locale as BabelLocale
from babel import UnknownLocaleError
from discord.ext import commands
from obsidion import __version__
from obsidion.core import i18n
from obsidion.core.i18n import cog_i18n
from obsidion.core.i18n import Translator
from obsidion.core.utils.chat_formatting import pagify
from obsidion.core.utils.predicates import MessagePredicate

log = logging.getLogger(__name__)

_ = Translator("Config", __file__)


@cog_i18n(_)
class Config(commands.Cog):
    def __init__(self, bot) -> None:
        """Init."""
        self.bot = bot

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

    @commands.group()
    async def account(self, ctx: commands.Context) -> None:
        """Link Minecraft account to Discord account."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @account.command(name="link")
    async def account_link(self, ctx: commands.Context, username: str) -> None:
        """Link account to discord account."""
        await ctx.channel.trigger_typing()
        profile_info = await self.bot.mojang_player(ctx.author, username)
        uuid: str = profile_info["uuid"]
        await self.bot._account_cache.set_account(ctx.author, uuid)
        
        await ctx.reply(f"Your account has been linked to {username}")

    @account.command(name="unlink")
    async def account_unlink(self, ctx: commands.Context) -> None:
        """Unlink minecraft account from discord account."""
        await self.bot._account_cache.set_account(ctx.author, None)
        await ctx.reply("Your account has been unlinked from any minecraft account")

    @commands.group()
    async def serverlink(self, ctx: commands.Context) -> None:
        """Link Minecraft server to Discord guild."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)
    
    @serverlink.command(name="link")
    async def serverlink_link(self, ctx, server: str) -> None:
        """Link Minecraft server to Discord guild."""
        await self.bot._guild_cache.set_server(ctx.guild, server)
        await ctx.reply(f"Your guild has been linked to {server}")

    @serverlink.command(name="unlink")
    async def serverlink_unlink(self, ctx: commands.Context) -> None:
        """Unlink minecraft server from discord guild."""
        await self.bot._guild_cache.set_server(ctx.guild, None)
        await ctx.reply("Your guild has been unlinked from any minecraft server")
