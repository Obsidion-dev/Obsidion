"""Development Commands."""
import ast
import asyncio
import inspect
import io
import re
import textwrap
import traceback
import types
from contextlib import redirect_stdout
from copy import copy
from typing import Optional

import aiohttp
import discord
from discord.ext import commands
from obsidion.core.i18n import cog_i18n
from obsidion.core.i18n import Translator

from .utils.chat_formatting import box
from .utils.chat_formatting import pagify
from .utils.predicates import MessagePredicate
from .utils.utils import send_interactive

START_CODE_BLOCK_RE = re.compile(r"^((```py)(?=\s)|(```))")

_ = Translator("Dev", __file__)


@cog_i18n(_)
class Dev(commands.Cog):
    """Development Commands."""

    def __init__(self, bot):
        """Init Development Cog."""
        self._last_result = None
        self.sessions = {}
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def load(self, ctx: commands.Context, *, module: str) -> None:
        """Loads a module."""
        try:
            self.bot.load_extension(f"obsidion.{module}")
        except commands.ExtensionError as e:
            await ctx.reply(
                f"{e.__class__.__name__}: {e}"
            )
        else:
            await ctx.reply(
                _("The cog `{module}` has been succesfully loaded").format(
                    module=module
                )
            )

    @commands.command()
    @commands.is_owner()
    async def unload(self, ctx: commands.Context, *, module: str) -> None:
        """Unloads a module."""
        try:
            self.bot.unload_extension(f"obsidion.{module}")
        except commands.ExtensionError as e:
            await ctx.reply(
                f"{e.__class__.__name__}: {e}"
            )
        else:
            await ctx.reply(
                _("The cog `{module}` has been succesfully unloaded").format(
                    module=module
                )
            )

    @commands.command(name="reload")
    @commands.is_owner()
    async def _reload(self, ctx: commands.Context, *, module: str) -> None:
        """Reloads a module."""
        try:
            self.bot.reload_extension(f"obsidion.{module}")
        except commands.ExtensionError as e:
            await ctx.reply(
                f"{e.__class__.__name__}: {e}"
            )
        else:
            await ctx.reply(
                _("The cog `{module}` has been succesfully reloaded").format(
                    module=module
                )
            )

    @staticmethod
    def async_compile(source, filename, mode):
        """Async Compile."""
        return compile(
            source, filename, mode, flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT, optimize=0
        )

    @staticmethod
    async def maybe_await(coro):
        """Maybe await code."""
        for _ in range(2):
            if inspect.isawaitable(coro):
                coro = await coro
            else:
                return coro
        return coro

    @staticmethod
    def cleanup_code(content):
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith("```") and content.endswith("```"):
            return START_CODE_BLOCK_RE.sub("", content)[:-3]

        # remove `foo`
        return content.strip("` \n")

    @staticmethod
    def get_syntax_error(e):
        """Format a syntax error to send to the user.

        Returns a string representation of the error formatted as a codeblock.
        """
        if e.text is None:
            return box("{0.__class__.__name__}: {0}".format(e), lang="py")
        return box(
            "{0.text}\n{1:>{0.offset}}\n{2}: {0}".format(e, "^", type(e).__name__),
            lang="py",
        )

    @staticmethod
    def get_pages(msg: str):
        """Pagify the given message for output to the user."""
        return pagify(msg, delims=["\n", " "], priority=True, shorten_by=10)

    @staticmethod
    def sanitize_output(ctx: commands.Context, input_: str) -> str:
        """Hides the bot's token from a string."""
        token = ctx.bot.http.token
        return re.sub(re.escape(token), "[EXPUNGED]", input_, re.I)

    @commands.command()
    @commands.is_owner()
    async def debug(self, ctx, *, code):
        """Evaluate a statement of python code.

        The bot will always respond with the return value of the code.
        If the return value of the code is a coroutine, it will be awaited,
        and the result of that will be the bot's response.

        Note: Only one statement may be evaluated. Using certain restricted
        keywords, e.g. yield, will result in a syntax error. For multiple
        lines or asynchronous code, see [p]repl or [p]eval.

        Environment Variables:
            ctx      - command invocation context
            bot      - bot object
            channel  - the current channel object
            author   - command author's member object
            message  - the command's message object
            discord  - discord.py library
            commands - discord.ext.commands
            _        - The result of the last dev command.
        """
        env = {
            "bot": ctx.bot,
            "ctx": ctx,
            "channel": ctx.channel,
            "author": ctx.author,
            "guild": ctx.guild,
            "message": ctx.message,
            "asyncio": asyncio,
            "aiohttp": aiohttp,
            "discord": discord,
            "commands": commands,
            "_": self._last_result,
            "__name__": "__main__",
        }

        code = self.cleanup_code(code)

        try:
            compiled = self.async_compile(code, "<string>", "eval")
            result = await self.maybe_await(eval(compiled, env))  # noqa: S307
        except SyntaxError as e:
            await ctx.send(self.get_syntax_error(e))
            return
        except Exception as e:
            await ctx.send(box("{}: {!s}".format(type(e).__name__, e), lang="py"))
            return

        self._last_result = result
        result = self.sanitize_output(ctx, str(result))

        await send_interactive(ctx, self.get_pages(result), box_lang="py")

    @commands.command(name="eval")
    @commands.is_owner()
    async def _eval(self, ctx, *, body: str):
        """Execute asynchronous code.

        This command wraps code into the body of an async function and then
        calls and awaits it. The bot will respond with anything printed to
        stdout, as well as the return value of the function.

        The code can be within a codeblock, inline code or neither, as long
        as they are not mixed and they are formatted correctly.

        Environment Variables:
            ctx      - command invocation context
            bot      - bot object
            channel  - the current channel object
            author   - command author's member object
            message  - the command's message object
            discord  - discord.py library
            commands - discord.ext.commands
            _        - The result of the last dev command.
        """
        env = {
            "bot": ctx.bot,
            "ctx": ctx,
            "channel": ctx.channel,
            "author": ctx.author,
            "guild": ctx.guild,
            "message": ctx.message,
            "asyncio": asyncio,
            "aiohttp": aiohttp,
            "discord": discord,
            "commands": commands,
            "_": self._last_result,
            "__name__": "__main__",
        }

        body = self.cleanup_code(body)
        stdout = io.StringIO()

        to_compile = "async def func():\n%s" % textwrap.indent(body, "  ")

        try:
            compiled = self.async_compile(to_compile, "<string>", "exec")
            exec(compiled, env)  # noqa: S102
        except SyntaxError as e:
            return await ctx.send(self.get_syntax_error(e))

        func = env["func"]
        result = None
        try:
            with redirect_stdout(stdout):
                result = await func()
        except Exception:
            printed = "{}{}".format(stdout.getvalue(), traceback.format_exc())
        else:
            printed = stdout.getvalue()

        if result is not None:
            self._last_result = result
            msg = "{}{}".format(printed, result)
        else:
            msg = printed
        msg = self.sanitize_output(ctx, msg)

        await send_interactive(ctx, self.get_pages(msg), box_lang="py")

    @commands.group(invoke_without_command=True)
    @commands.is_owner()
    async def repl(self, ctx):  # noqa C901
        """Open an interactive REPL.

        The REPL will only recognise code as messages which start with a
        backtick. This includes codeblocks, and as such multiple lines can be
        evaluated.
        """
        variables = {
            "ctx": ctx,
            "bot": ctx.bot,
            "message": ctx.message,
            "guild": ctx.guild,
            "channel": ctx.channel,
            "author": ctx.author,
            "asyncio": asyncio,
            "__name__": "__main__",
        }

        if ctx.channel.id in self.sessions:
            if self.sessions[ctx.channel.id]:
                await ctx.send(
                    _(
                        "Already running a REPL session in"
                        " this channel. Exit it with `quit`."
                    )
                )
            else:
                await ctx.send(
                    _(
                        "Already running a REPL session in this"
                        " channel. Resume the REPL with `{}repl resume`."
                    ).format(ctx.prefix)
                )
            return

        self.sessions[ctx.channel.id] = True
        await ctx.send(
            _(
                "Enter code to execute or evaluate. `exit()`"
                " or `quit` to exit. `{}repl pause` to pause."
            ).format(ctx.prefix)
        )

        while True:
            try:
                response = await ctx.bot.wait_for(
                    "message", check=MessagePredicate.regex(r"^`", ctx), timeout=60.0
                )
            except asyncio.TimeoutError:
                await ctx.send("Stopping")
                return

            if not self.sessions[ctx.channel.id]:
                continue

            cleaned = self.cleanup_code(response.content)

            if cleaned in ("quit", "exit", "exit()"):
                await ctx.send(("Exiting."))
                del self.sessions[ctx.channel.id]
                return

            executor = None
            if cleaned.count("\n") == 0:
                # single statement, potentially 'eval'
                try:
                    code = self.async_compile(cleaned, "<repl session>", "eval")
                except SyntaxError:
                    pass
                else:
                    executor = eval

            if executor is None:
                try:
                    code = self.async_compile(cleaned, "<repl session>", "exec")
                except SyntaxError as e:
                    await ctx.send(self.get_syntax_error(e))
                    continue

            variables["message"] = response

            stdout = io.StringIO()

            msg = ""

            try:
                with redirect_stdout(stdout):
                    if executor is None:
                        result = types.FunctionType(code, variables)()
                    else:
                        result = executor(code, variables)
                    result = await self.maybe_await(result)
            except Exception:
                value = stdout.getvalue()
                msg = "{}{}".format(value, traceback.format_exc())
            else:
                value = stdout.getvalue()
                if result is not None:
                    msg = "{}{}".format(value, result)
                    variables["_"] = result
                elif value:
                    msg = "{}".format(value)

            msg = self.sanitize_output(ctx, msg)

            try:
                await send_interactive(ctx, self.get_pages(msg), box_lang="py")
            except discord.Forbidden:
                pass
            except discord.HTTPException as e:
                await ctx.send(("Unexpected error: `{}`").format(e))

    @repl.command(aliases=["resume"])
    async def pause(self, ctx, toggle: Optional[bool] = None):
        """Pauses/resumes the REPL running in the current channel"""
        if ctx.channel.id not in self.sessions:
            await ctx.send(
                _("There is no currently running REPL session in this channel.")
            )
            return

        if toggle is None:
            toggle = not self.sessions[ctx.channel.id]
        self.sessions[ctx.channel.id] = toggle

        if toggle:
            await ctx.send(_("The REPL session in this channel has been resumed."))
        else:
            await ctx.send(_("The REPL session in this channel is now paused."))

    @commands.command()
    @commands.is_owner()
    async def mock(self, ctx, user: discord.Member, *, command):
        """Mock another user invoking a command.

        The prefix must not be entered.
        """
        msg = copy(ctx.message)
        msg.author = user
        msg.content = ctx.prefix + command

        ctx.bot.dispatch("message", msg)

    @commands.command(name="mockmsg")
    @commands.is_owner()
    async def mock_msg(self, ctx, user: discord.Member, *, content: str):
        """Dispatch a message event as if it were sent by a different user.

        Only reads the raw content of the message. Attachments, embeds etc. are
        ignored.
        """
        old_author = ctx.author
        old_content = ctx.message.content
        ctx.message.author = user
        ctx.message.content = content

        ctx.bot.dispatch("message", ctx.message)

        # If we change the author and content back too quickly,
        # the bot won't process the mocked message in time.
        await asyncio.sleep(2)
        ctx.message.author = old_author
        ctx.message.content = old_content
