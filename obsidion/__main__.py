"""Initialise and run the bot."""
import logging

from discord import Activity
from discord import ActivityType
from discord import AllowedMentions
from discord import Intents
from obsidion import _update_event_loop_policy
from obsidion.core import get_settings
from obsidion.core.bot import Obsidion
from obsidion.core.help import Help
from discord_slash import SlashCommand
from discord_slash import SlashContext

_update_event_loop_policy()

log = logging.getLogger("obsidion")


def main():
    """Main initialisation script."""
    # So no one can abuse the bot to mass mention
    allowed_mentions = AllowedMentions(everyone=False, roles=False, users=True)

    # We don't need many mentions so this is the bare minimum we eed
    intents = Intents.none()
    intents.messages = True
    intents.guilds = True
    intents.reactions = True

    activity = activity = Activity(
        name=get_settings().ACTIVITY,
        type=ActivityType.watching,
    )

    args = {
        "case_insensitive": True,
        "description": "",
        "self_bot": False,
        "help_command": Help(),
        "owner_ids": [],
        "activity": activity,
        "intents": intents,
        "allowed_mentions": allowed_mentions,
    }

    obsidion = Obsidion(**args)

    log.info("Ready to go, building everything")
    slash = SlashCommand(obsidion, sync_commands=True, sync_on_cog_reload=True)
    log.info("Initialised slash commands")
    obsidion.run(get_settings().DISCORD_TOKEN)

    log.info("Obsidion shutting down, cleaning up")

    log.info("Cleanup complete")


if __name__ == "__main__":
    """Run the bot."""
    main()
