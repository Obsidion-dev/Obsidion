from .facts import Facts


def setup(bot) -> None:
    """Setup."""
    bot.add_cog(Facts(bot))
