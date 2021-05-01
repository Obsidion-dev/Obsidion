"""Fun."""
from .fun import Fun


def setup(bot) -> None:
    """Setup."""
    bot.add_cog(Fun(bot))
