"""Info."""
from .rcon import Rcon


def setup(bot) -> None:
    """Setup."""
    bot.add_cog(Rcon(bot))
