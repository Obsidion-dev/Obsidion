"""Info."""
from .news import News


def setup(bot) -> None:
    """Setup."""
    bot.add_cog(News(bot))
