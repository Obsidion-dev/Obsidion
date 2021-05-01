import discord as _discord

from .config import get_settings

__all__ = ["get_settings"]


# Prevent discord PyNaCl missing warning as it will never be loaded
_discord.voice_client.VoiceClient.warn_nacl = False
