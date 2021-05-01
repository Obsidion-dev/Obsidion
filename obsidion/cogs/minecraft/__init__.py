"""Minecraft."""
from .minecraft import Minecraft


def setup(bot) -> None:
    """Setup."""
    bot.add_cog(Minecraft(bot))
