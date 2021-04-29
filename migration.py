"""Initialise and run the bot."""
import logging

from discord import Activity
from discord import ActivityType
from discord import Intents
from obsidion.core.config import get_settings

import asyncpg

log = logging.getLogger("obsidion")
import discord


# We don't need many mentions so this is the bare minimum we eed
intents = Intents.none()
intents.messages = True
intents.guilds = True
intents.reactions = True

activity = Activity(
    name="Running Database Migration",
    type=ActivityType.watching,
)

client = discord.Client(intents=intents, activity=activity)

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    db = await asyncpg.create_pool(str(get_settings().DB))
    for guild in client.guilds:
        await db.execute(
                "INSERT INTO guild (id, prefix) VALUES ($1, $2)",
                guild.id,
                "/",
            )
        log.info("Setting %s to default prefix of /", guild.id)
    log.info("Finished Migration")
    db.close()
    client.logout()

client.run(get_settings().DISCORD_TOKEN)
