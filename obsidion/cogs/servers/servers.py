"""Images cog."""
import logging

import discord
from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.utils.manage_commands import create_option
from obsidion.core import get_settings
from obsidion.core.i18n import cog_i18n
from obsidion.core.i18n import Translator


log = logging.getLogger(__name__)

_ = Translator("Servers", __file__)


@cog_i18n(_)
class Servers(commands.Cog):
    def __init__(self, bot) -> None:
        """Init."""
        self.bot = bot
