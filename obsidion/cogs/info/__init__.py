"""Info."""
from .info import Info


def setup(bot) -> None:
    """Setup."""
    bot.add_cog(Info(bot))
