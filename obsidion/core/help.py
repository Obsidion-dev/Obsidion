import itertools
from typing import Dict

import discord
from discord.ext.commands import Command
from discord.ext.commands import HelpCommand
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

from .i18n import Translator

_ = Translator("Help", __file__)


class HelpQueryNotFound(ValueError):
    """Raised when a HelpSession Query doesn't match a command or cog.

    Contains the custom attribute of ``possible_matches``.
    Instances of this object contain a dictionary of any command(s)
    that were close to matching the query, where keys are the possible
    matched command names and values are the likeness match scores.
    """

    def __init__(self, arg: str, possible_matches: Dict[str, int]) -> None:
        """Init."""
        super().__init__(arg)
        self.possible_matches = possible_matches


class Help(HelpCommand):
    """An implementation of a help command with minimal output.
    This inherits from :class:`HelpCommand`.
    Attributes
    ------------
    sort_commands: :class:`bool`
        Whether to sort the commands in the output alphabetically. Defaults to ``True``.
    commands_heading: :class:`str`
        The command list's heading string
        used when the help command is invoked with a category name.
        Useful for i18n. Defaults to ``"Commands"``
    aliases_heading: :class:`str`
        The alias list's heading string used to
        list the aliases of the command. Useful for i18n.
        Defaults to ``"Aliases:"``.
    dm_help: Optional[:class:`bool`]
        A tribool that indicates if the help command should DM the user instead of
        sending it to the channel it received it from. If the boolean is set to
        ``True``, then all help output is DM'd. If ``False``, none of the help
        output is DM'd. If ``None``, then the bot will only DM when the help
        message becomes too long (dictated by
        more than :attr:`dm_help_threshold` characters).
        Defaults to ``False``.
    dm_help_threshold: Optional[:class:`int`]
        The number of characters the paginator must accumulate
        before getting DM'd to the
        user if :attr:`dm_help` is set to ``None``. Defaults to 1000.
    no_category: :class:`str`
        The string used when there is a command which does
        not belong to any category(cog).
        Useful for i18n. Defaults to ``"No Category"``
    """

    def __init__(self, **options):
        self.sort_commands = options.pop("sort_commands", True)
        self.commands_heading = options.pop("commands_heading", "Commands")
        self.dm_help = options.pop("dm_help", False)
        self.dm_help_threshold = options.pop("dm_help_threshold", 1000)
        self.aliases_heading = options.pop("aliases_heading", "Aliases:")
        self.no_category = options.pop("no_category", "Core")
        self.embed = options.pop("embed", None)

        if self.embed is None:
            self.embed = discord.Embed()

        super().__init__(**options)

    async def get_all_help_choices(self) -> set:
        """Get all the possible options for getting help in the bot.

        Returns:
            set: all help options

        This will only display commands the author has permission to run.
        These include:
        - Category names
        - Cog names
        - Group command names (and aliases)
        - Command names (and aliases)
        - Subcommand names (with parent group and aliases for subcommand,
            but not including aliases for group)

        Options and choices are case sensitive.
        """
        # first get all commands including subcommands and full command name aliases
        choices = set()
        for command in await self.filter_commands(self.context.bot.walk_commands()):
            # the the command or group name
            choices.add(str(command))

            if isinstance(command, Command):
                # all aliases if it's just a command
                choices.update(command.aliases)
            else:
                # otherwise we need to add the parent name in
                choices.update(
                    f"{command.full_parent_name} {alias}" for alias in command.aliases
                )

        # all cog names
        choices.update(self.context.bot.cogs)

        # all category names
        choices.update(
            cog.category
            for cog in self.context.bot.cogs.values()
            if hasattr(cog, "category")
        )
        return choices

    async def subcommand_not_found(self, command, string: str) -> HelpQueryNotFound:
        """Redirects the error to `command_not_found`."""
        return await self.command_not_found(f"{command.qualified_name} {string}")

    async def send_error_message(self, error: HelpQueryNotFound) -> None:
        """Send the error message to the channel."""
        self.embed.colour = discord.Colour.red()
        self.embed.title = str(error)

        ctx = self.context
        bot = ctx.bot
        if bot.description:
            self.embed.description = bot.description

        self.embed.set_author(name="Obsidion Help", icon_url=ctx.me.avatar_url)
        ending = self.get_ending_note()
        if ending:
            self.embed.set_footer(text=ending)

        if getattr(error, "possible_matches", None):
            matches = "\n".join(f"`{match}`" for match in error.possible_matches)
            self.embed.description = f"**Did you mean:**\n{matches}"

            await self.send_embed()

    async def command_not_found(self, string: str) -> HelpQueryNotFound:
        """Handles when a query does not match a valid command, group, cog or category.

        Args:
            string (str): command

        Returns:
            HelpQueryNotFound: command not found.
        """
        choices = await self.get_all_help_choices()
        result = process.extractBests(
            string, choices, scorer=fuzz.ratio, score_cutoff=60
        )

        return HelpQueryNotFound(f'Query "{string}" not found.', dict(result))

    async def send_embed(self):
        """A helper utility to send the page output
        from :attr:`paginator` to the destination."""
        await self.context.send(embed=self.embed)

    def get_opening_note(self):
        """Returns help command's opening note.
        This is mainly useful to override for i18n purposes.
        The default implementation returns ::
            Use `{prefix}{command_name} [command]` for more info on a command.
            You can also use `{prefix}{command_name}
            [category]` for more info on a category.
        Returns
        -------
        :class:`str`
            The help command opening note.
        """
        return None

    def get_command_signature(self, command):
        return "%s%s %s" % (
            self.prefix,
            command.qualified_name,
            command.signature,
        )

    def get_ending_note(self):
        """Return the help command's ending note.
        This is mainly useful to override for i18n purposes.
        The default implementation does nothing.
        Returns
        -------
        :class:`str`
            The help command ending note.
        """
        command_name = self.context.invoked_with
        return (
            "Use {0}{1} [command] for more info on a command.\n"
            "You can also use {0}{1} [category] for more info on a category.".format(
                self.prefix, command_name
            )
        )

    def add_bot_commands_formatting(self, commands, heading):
        """Adds the minified bot heading with commands to the output.
        The formatting should be added to the :attr:`paginator`.
        The default implementation is a bold underline heading followed
        by commands separated by an EN SPACE (U+2002) in the next line.
        Parameters
        -----------
        commands: Sequence[:class:`Command`]
            A list of commands that belong to the heading.
        heading: :class:`str`
            The heading to add to the line.
        """
        if commands:
            # U+2002 Middle Dot
            joined = "`, `".join(c.name for c in commands)
            self.embed.add_field(name=heading, value=f"`{joined}`", inline=False)

    def add_subcommand_formatting(self, command):
        """Adds formatting information on a subcommand.
        The formatting should be added to the :attr:`paginator`.
        The default implementation is the prefix and the :attr:`Command.qualified_name`
        optionally followed by an En dash and the command's :attr:`Command.short_doc`.
        Parameters
        -----------
        command: :class:`Command`
            The command to show information of.
        """
        self.embed.add_field(
            name=f"{self.prefix}{command.qualified_name}",
            value=command.short_doc,
        )

    def add_command_formatting(self, command):
        """A utility function to format commands and groups.
        Parameters
        ------------
        command: :class:`Command`
            The command to format.
        """
        description = (
            f"Name: `{command.qualified_name}`\n" f"Category: `{command.cog_name}`\n"
        )
        if command.aliases:
            description += f'Aliases: `{"`, `".join(command.aliases)}`'

        self.embed.add_field(
            name=command.qualified_name,
            value=description,
            inline=False,
        )

    async def prepare_help_command(self, ctx, command):
        self.embed.color = ctx.bot.color
        self.prefix = (
            await self.context.bot._prefix_cache.get_prefixes(self.context.guild)
        )[0]
        await super().prepare_help_command(ctx, command)

    async def send_bot_help(self, mapping):
        ctx = self.context
        bot = ctx.bot
        if bot.description:
            self.embed.description = bot.description

        ending = self.get_ending_note()
        if ending:
            self.embed.set_footer(text=self.get_ending_note())

        no_category = self.no_category

        def get_category(command, *, no_category=no_category):
            cog = command.cog
            return cog.qualified_name if cog is not None else no_category

        filtered = await self.filter_commands(bot.commands, sort=True, key=get_category)
        to_iterate = itertools.groupby(filtered, key=get_category)

        self.embed.set_author(name="Obsidion Help", icon_url=ctx.me.avatar_url)

        for category, commands in to_iterate:
            commands = (
                sorted(commands, key=lambda c: c.name)
                if self.sort_commands
                else list(commands)
            )

            self.add_bot_commands_formatting(commands, category)
        await self.send_embed()

    async def send_cog_help(self, cog):
        bot = self.context.bot
        if bot.description:
            self.embed.title = bot.description
        ending = self.get_ending_note()
        if ending:
            self.embed.set_footer(text=ending)

        if cog.description:
            self.embed.description = cog.description

        filtered = await self.filter_commands(
            cog.get_commands(), sort=self.sort_commands
        )
        if filtered:
            self.embed.set_author(
                name=f"Obsidion {cog.qualified_name} Help",
                icon_url=self.context.me.avatar_url,
            )
            for command in filtered:
                self.add_subcommand_formatting(command)
        await self.send_embed()

    async def send_group_help(self, group):
        if group.help:
            self.embed.description = group.help
        self.embed.add_field(
            name="Usage",
            value=f"`{self.prefix}{group.qualified_name} {group.signature}`",
        )
        ending = self.get_ending_note()
        if ending:
            self.embed.set_footer(text=ending)
        self.add_command_formatting(group)
        filtered = await self.filter_commands(group.commands, sort=self.sort_commands)
        if filtered:
            for command in filtered:
                self.add_subcommand_formatting(command)
        self.embed.set_author(
            name=f"Obsidion {group.qualified_name} Help",
            icon_url=self.context.me.avatar_url,
        )
        await self.send_embed()

    async def send_command_help(self, command):
        if command.help:
            self.embed.description = command.help
        self.embed.add_field(
            name="Usage",
            value=f"`{self.prefix}{command.qualified_name} {command.signature}`",
        )
        ending = self.get_ending_note()
        if ending:
            self.embed.set_footer(text=ending)
        self.add_command_formatting(command)
        self.embed.set_author(
            name=f"Obsidion {command.qualified_name} Help",
            icon_url=self.context.me.avatar_url,
        )
        await self.send_embed()
