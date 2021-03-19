"""Config."""
from .config import Config


def setup(bot) -> None:
    """Setup."""
    bot.add_cog(Config(bot))
