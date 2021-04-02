"""Info."""
from .rcon import NewRcons


def setup(bot) -> None:
    """Setup."""
    bot.add_cog(Rcon(bot))
