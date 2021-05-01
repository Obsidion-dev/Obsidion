from .botlist import Botlist


def setup(bot) -> None:
    """Setup."""
    bot.add_cog(Botlist(bot))
