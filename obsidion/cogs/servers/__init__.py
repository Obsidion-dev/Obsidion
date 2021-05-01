"""Info."""
from .servers import Servers


def setup(bot) -> None:
    """Setup."""
    bot.add_cog(Servers(bot))
