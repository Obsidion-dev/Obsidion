"""Botlist."""
from obsidion.core import get_settings
import logging


from discord.ext import commands
import dbl
from discord.ext import tasks

log = logging.getLogger(__name__)

class Botlist(commands.Cog):
    def __init__(self, bot) -> None:
        """Init."""
        self.bot = bot
        self.dblpy = None
        self.post_stats.start()

    @tasks.loop(minutes=30.0)
    async def post_stats(self):
        await self.bot.wait_until_ready()
        if self.dblpy is None:
            self.dblpy = dbl.DBLClient(self.bot, get_settings().DBL_TOKEN, autopost=True)
        await self.post_discordbotlist()
        await self.post_botsfordiscord()
        await self.post_discordboats()
        await self.post_discordlabs()

    async def on_guild_post(self):
        log.info("Top.gg guild count posted.")

    async def post_discordbotlist(self):
        headers = {
            "Content-Type": "application/json",
            "Authorization": get_settings().DISCORDBOTLIST_TOKEN,
        }
        json = {"server_count": len(self.bot.guilds)}
        await self.bot.http_session.post(f"https://discordbotlist.com/api/v1/bots/{self.bot.user.id}/stats", headers=headers, json=json)

    async def post_botsfordiscord(self):
        headers = {
            "Content-Type": "application/json",
            "Authorization": get_settings().BOTSFORDISCORD_TOKEN,
        }
        json = {"server_count": len(self.bot.guilds)}

        await self.bot.http_session.post(
            f"https://botsfordiscord.com/api/bot/{self.bot.user.id}",
            headers=headers,
            json=json,
        )

    async def post_discordboats(self):
        headers = {
            "Authorization": get_settings().DISCORDBOATS_TOKEN,
        }
        json = {"server_count": len(self.bot.guilds)}

        await self.bot.http_session.post(
            f"https://discord.boats/api/bot/{self.bot.user.id}",
            headers=headers,
            json=json,
        )

    async def post_discordlabs(self):
        headers = {
            "token": get_settings().DISCORDLABS_TOKEN,
        }
        json = {"server_count": len(self.bot.guilds)}

        await self.bot.http_session.post(
            f"https://bots.discordlabs.org/v2/bot/{self.bot.user.id}/stats",
            headers=headers,
            json=json,
        )