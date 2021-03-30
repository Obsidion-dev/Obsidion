import typing
import asyncio
import discord
from contextlib import suppress
from discord.ext import commands
from . import http
from . import error
from . import model
from discord.ext.commands.core import Group, Command, wrap_callback
from discord.ext.commands.errors import CommandError



class SlashContext:
    """
    Context of the slash command.\n
    Kinda similar with discord.ext.commands.Context.

    .. warning::
        Do not manually init this model.

    :ivar message: Message that invoked the slash command.
    :ivar name: Name of the command.
    :ivar subcommand_name: Subcommand of the command.
    :ivar subcommand_group: Subcommand group of the command.
    :ivar interaction_id: Interaction ID of the command message.
    :ivar command_id: ID of the command.
    :ivar bot: discord.py client.
    :ivar _http: :class:`.http.SlashCommandRequest` of the client.
    :ivar _logger: Logger instance.
    :ivar deffered: Whether the command is current deffered (loading state)
    :ivar _deffered_hidden: Internal var to check that state stays the same
    :ivar responded: Whether you have responded with a message to the interaction.
    :ivar guild_id: Guild ID of the command message. If the command was invoked in DM, then it is ``None``
    :ivar author_id: User ID representing author of the command message.
    :ivar channel_id: Channel ID representing channel of the command message.
    :ivar author: User or Member instance of the command invoke.
    """

    def __init__(self,
                 _http: http.SlashCommandRequest,
                 _json: dict,
                 _discord: typing.Union[discord.Client, commands.Bot],
                 logger):
        self.__token = _json["token"]
        self.message = None # Should be set later.
        self.name = self.command = self.invoked_with = _json["data"]["name"]
        self.subcommand_name = self.invoked_subcommand = self.subcommand_passed = None
        self.subcommand_group = self.invoked_subcommand_group = self.subcommand_group_passed = None
        self.interaction_id = _json["id"]
        self.command_id = _json["data"]["id"]
        self._http = _http
        self.bot = _discord
        self._logger = logger
        self.deffered = False
        self.responded = False
        self._deffered_hidden = False  # To check if the patch to the deffered response matches
        self.guild_id = int(_json["guild_id"]) if "guild_id" in _json.keys() else None
        self.author_id = int(_json["member"]["user"]["id"] if "member" in _json.keys() else _json["user"]["id"])
        self.channel_id = int(_json["channel_id"])
        if self.guild:
            self.author = discord.Member(data=_json["member"], state=self.bot._connection, guild=self.guild)
        elif self.guild_id:
            self.author = discord.User(data=_json["member"]["user"], state=self.bot._connection)
        else:
            self.author = discord.User(data=_json["user"], state=self.bot._connection)
        self.prefix = "/"

    @property
    def guild(self) -> typing.Optional[discord.Guild]:
        """
        Guild instance of the command invoke. If the command was invoked in DM, then it is ``None``

        :return: Optional[discord.Guild]
        """
        return self.bot.get_guild(self.guild_id) if self.guild_id else None

    @property
    def channel(self) -> typing.Optional[typing.Union[discord.TextChannel, discord.DMChannel]]:
        """
        Channel instance of the command invoke.

        :return: Optional[Union[discord.abc.GuildChannel, discord.abc.PrivateChannel]]
        """
        return self.bot.get_channel(self.channel_id)

    async def defer(self, hidden: bool = False):
        """
        'Deferes' the response, showing a loading state to the user

        :param hidden: Whether the deffered response should be ephemeral . Default ``False``.
        """
        if self.deffered or self.responded:
            raise error.AlreadyResponded("You have already responded to this command!")
        base = {"type": 5}
        if hidden:
            base["data"] = {"flags": 64}
            self._deffered_hidden = True
        await self._http.post_initial_response(base, self.interaction_id, self.__token)
        self.deffered = True

    async def send(self,
                   content: str = "", *,
                   embed: discord.Embed = None,
                   embeds: typing.List[discord.Embed] = None,
                   tts: bool = False,
                   file: discord.File = None,
                   files: typing.List[discord.File] = None,
                   allowed_mentions: discord.AllowedMentions = None,
                   hidden: bool = False,
                   delete_after: float = None) -> model.SlashMessage:
        """
        Sends response of the slash command.

        .. note::
            - Param ``hidden`` doesn't support embed and file.

        .. warning::
            - Since Release 1.0.9, this is completely changed. If you are migrating from older version, please make sure to fix the usage.
            - You can't use both ``embed`` and ``embeds`` at the same time, also applies to ``file`` and ``files``.
            - You cannot send files in the initial response

        :param content:  Content of the response.
        :type content: str
        :param embed: Embed of the response.
        :type embed: discord.Embed
        :param embeds: Embeds of the response. Maximum 10.
        :type embeds: List[discord.Embed]
        :param tts: Whether to speak message using tts. Default ``False``.
        :type tts: bool
        :param file: File to send.
        :type file: discord.File
        :param files: Files to send.
        :type files: List[discord.File]
        :param allowed_mentions: AllowedMentions of the message.
        :type allowed_mentions: discord.AllowedMentions
        :param hidden: Whether the message is hidden, which means message content will only be seen to the author.
        :type hidden: bool
        :param delete_after: If provided, the number of seconds to wait in the background before deleting the message we just sent. If the deletion fails, then it is silently ignored.
        :type delete_after: float
        :return: Union[discord.Message, dict]
        """
        if embed and embeds:
            raise error.IncorrectFormat("You can't use both `embed` and `embeds`!")
        if embed:
            embeds = [embed]
        if embeds:
            if not isinstance(embeds, list):
                raise error.IncorrectFormat("Provide a list of embeds.")
            elif len(embeds) > 10:
                raise error.IncorrectFormat("Do not provide more than 10 embeds.")
        if file and files:
            raise error.IncorrectFormat("You can't use both `file` and `files`!")
        if file:
            files = [file]
        if delete_after and hidden:
            raise error.IncorrectFormat("You can't delete a hidden message!")

        base = {
            "content": content,
            "tts": tts,
            "embeds": [x.to_dict() for x in embeds] if embeds else [],
            "allowed_mentions": allowed_mentions.to_dict() if allowed_mentions
            else self.bot.allowed_mentions.to_dict() if self.bot.allowed_mentions else {}
        }
        if hidden:
            if embeds or files:
                self._logger.warning("Embed/File is not supported for `hidden`!")
            base["flags"] = 64
        
        initial_message = False
        if not self.responded:
            initial_message = True
            if files:
                raise error.IncorrectFormat("You cannot send files in the initial response!")
            if self.deffered:
                if self._deffered_hidden != hidden:
                    self._logger.warning(
                        "Deffered response might not be what you set it to! (hidden / visible) "
                        "This is because it was deffered in a different state"
                    )
                resp = await self._http.edit(base, self.__token)
                self.deffered = False
            else:
                json_data = {
                    "type": 4,
                    "data": base
                }
                await self._http.post_initial_response(json_data, self.interaction_id, self.__token)
                if not hidden:
                    resp = await self._http.edit({}, self.__token)
                else:
                    resp = {}
            self.responded = True
        else:
            resp = await self._http.post_followup(base, self.__token, files=files)
        if not hidden:
            smsg = model.SlashMessage(state=self.bot._connection,
                                      data=resp,
                                      channel=self.channel or discord.Object(id=self.channel_id),
                                      _http=self._http,
                                      interaction_token=self.__token)
            if delete_after:
                self.bot.loop.create_task(smsg.delete(delay=delete_after))
            if initial_message:
                self.message = smsg
            return smsg
        else:
            return resp

    async def send_help(self, command=None):
        """send_help(entity=<bot>)
        |coro|
        Shows the help command for the specified entity if given.
        The entity can be a command or a cog.
        If no entity is given, then it'll show help for the
        entire bot.
        If the entity is a string, then it looks up whether it's a
        :class:`Cog` or a :class:`Command`.
        .. note::
            Due to the way this function works, instead of returning
            something similar to :meth:`~.commands.HelpCommand.command_not_found`
            this returns :class:`None` on bad input or no help command.
        Parameters
        ------------
        entity: Optional[Union[:class:`Command`, :class:`Cog`, :class:`str`]]
            The entity to show help for.
        Returns
        --------
        Any
            The result of the help command, if any.
        """
        bot = self.bot
        cmd = bot.help_command

        cmd = cmd.copy()
        cmd.context = self
        if command == None:
            await cmd.prepare_help_command(self, None)
            mapping = cmd.get_bot_mapping()
            injected = wrap_callback(cmd.send_bot_help)
            try:
                return await injected(mapping)
            except CommandError as e:
                await cmd.on_help_command_error(self, e)
                return None
        entity = command
        if entity is None:
            return None
        if isinstance(entity, str):
            entity = bot.get_cog(entity) or bot.get_command(entity)
        try:
            entity.qualified_name
        except AttributeError:
            # if we're here then it's not a cog, group, or command.
            return None
        await cmd.prepare_help_command(self, entity.qualified_name)
        try:
            if hasattr(entity, '__cog_commands__'):
                injected = wrap_callback(cmd.send_cog_help)
                return await injected(entity)
            elif isinstance(entity, Group):
                injected = wrap_callback(cmd.send_group_help)
                return await injected(entity)
            elif isinstance(entity, Command):
                injected = wrap_callback(cmd.send_command_help)
                return await injected(entity)
            else:
                return None
        except CommandError as e:
            await cmd.on_help_command_error(self, e)

    # @property
    # def valid(self):
    #     """:class:`bool`: Checks if the invocation context is valid to be invoked with."""
    #     return self.prefix is not None and self.command is not None

    # async def _get_channel(self):
    #     return self.channel

    # @property
    # def cog(self):
    #     """Optional[:class:`.Cog`]: Returns the cog associated with this context's command. None if it does not exist."""

    #     if self.command is None:
    #         return None
    #     return self.command.cog

    # @discord.utils.cached_property
    # def guild(self):
    #     """Optional[:class:`.Guild`]: Returns the guild associated with this context's command. None if not available."""
    #     return self.message.guild

    # @discord.utils.cached_property
    # def channel(self):
    #     """Union[:class:`.abc.Messageable`]: Returns the channel associated with this context's command.
    #     Shorthand for :attr:`.Message.channel`.
    #     """
    #     return self.message.channel

    # @discord.utils.cached_property
    # def author(self):
    #     """Union[:class:`~discord.User`, :class:`.Member`]:
    #     Returns the author associated with this context's command. Shorthand for :attr:`.Message.author`
    #     """
    #     return self.message.author

    @discord.utils.cached_property
    def me(self):
        """Union[:class:`.Member`, :class:`.ClientUser`]:
        Similar to :attr:`.Guild.me` except it may return the :class:`.ClientUser` in private message contexts.
        """
        return self.guild.me if self.guild is not None else self.bot.user

    # @property
    # def voice_client(self):
    #     r"""Optional[:class:`.VoiceProtocol`]: A shortcut to :attr:`.Guild.voice_client`\, if applicable."""
    #     g = self.guild
    #     return g.voice_client if g else None