"""The checks in this module run on every command."""
from __future__ import annotations

from discord.ext import commands


def init_global_checks(bot):
    """Initiate global checks."""

    @bot.check_once
    async def check_message_is_eligible_as_command(ctx: commands.Context) -> bool:
        """Check wether message is eligible."""
        return await ctx.bot.message_eligible_as_command(ctx.message)
