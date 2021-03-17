"""Setup hypixel."""
from .hypixel import Hypixel


def setup(bot) -> None:
    """Setup."""
    bot.add_cog(Hypixel(bot))
