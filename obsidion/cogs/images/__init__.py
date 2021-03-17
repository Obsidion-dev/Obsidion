"""Setup images."""
from .images import Images


def setup(bot) -> None:
    """Setup."""
    bot.add_cog(Images(bot))
