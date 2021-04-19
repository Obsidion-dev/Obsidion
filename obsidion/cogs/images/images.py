"""Images cog."""
import logging
from typing import Optional
from typing import Union

import discord
from discord.ext import commands
from discord_slash import cog_ext
from discord_slash import SlashContext
from discord_slash.utils.manage_commands import create_option
from obsidion.core import get_settings
from obsidion.core.i18n import cog_i18n
from obsidion.core.i18n import Translator


log = logging.getLogger(__name__)

_ = Translator("Images", __file__)


@cog_i18n(_)
class Images(commands.Cog):
    def __init__(self, bot) -> None:
        """Init."""
        self.bot = bot

    @commands.command()
    async def achievement(
        self,
        ctx: Union[commands.Context, SlashContext],
        block_name: str,
        title: str,
        *,
        text: str,
    ) -> None:
        """Create your very own custom Minecraft achievements."""
        text = text.replace(" ", "%20")
        embed = discord.Embed(color=self.bot.color)
        embed.set_author(
            name=_("Obsidion Advancement Generator"), icon_url=self.bot.user.avatar_url
        )
        embed.set_image(
            url=(
                f"{get_settings().API_URL}/images/advancement?item={block_name}&title={title}&text={text}"
            )
        )
        await ctx.send(embed=embed)

    # @commands.command()
    async def sign(
        self,
        ctx: Union[commands.Context, SlashContext],
        *,
        text: str,
    ) -> None:
        """Create a Minecraft sign with custom text."""
        split = text.replace(" ", "%20").split("|")
        line1 = split[0] if len(split) >= 1 else "%20"
        line2 = split[1] if len(split) >= 2 else "%20"
        line3 = split[2] if len(split) >= 3 else "%20"
        line4 = split[3] if len(split) >= 4 else "%20"
        embed = discord.Embed(color=self.bot.color)
        embed.set_author(
            name=_("Obsidion Sign Generator"), icon_url=self.bot.user.avatar_url
        )
        embed.set_image(
            url=(
                f"{get_settings().API_URL}/images/sign?line1={line1}&line2={line2}&line3={line3}&line4={line4}"
            )
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def avatar(
        self, ctx: Union[commands.Context, SlashContext], username: Optional[str] = None
    ) -> None:
        """Renders a Minecraft players face."""
        await self.render(ctx, "face", username)

    @cog_ext.cog_slash(
        name="avatar",
        options=[
            create_option(
                name="username",
                description="Username of account defaults to linked account.",
                option_type=3,
                required=False,
            )
        ],
    )
    async def slash_avatar(self, ctx: SlashContext, username: str = None) -> None:
        """Renders a Minecraft players face."""
        await ctx.defer()
        await self.avatar(ctx, username)

    @commands.command()
    async def skull(
        self, ctx: Union[commands.Context, SlashContext], username: Optional[str] = None
    ) -> None:
        """Renders a Minecraft players skull."""
        await self.render(ctx, "head", username)

    @cog_ext.cog_slash(
        name="skull",
        options=[
            create_option(
                name="username",
                description="Username of account defaults to linked account.",
                option_type=3,
                required=False,
            )
        ],
    )
    async def slash_skull(self, ctx: SlashContext, username: str = None) -> None:
        """Renders a Minecraft players skull."""
        await ctx.defer()
        await self.skull(ctx, username)

    @commands.command()
    async def skin(
        self, ctx: Union[commands.Context, SlashContext], username: Optional[str] = None
    ) -> None:
        """Renders a Minecraft players skin."""
        await self.render(ctx, "full", username)

    @cog_ext.cog_slash(
        name="skin",
        options=[
            create_option(
                name="username",
                description="Username of account defaults to linked account.",
                option_type=3,
                required=False,
            )
        ],
    )
    async def slash_skin(self: SlashContext, ctx, username: str = None) -> None:
        """Renders a Minecraft players skin."""
        await ctx.defer()
        await self.skin(ctx, username)

    @commands.command()
    async def bust(
        self, ctx: Union[commands.Context, SlashContext], username: Optional[str] = None
    ) -> None:
        """Renders a Minecraft players bust."""
        await self.render(ctx, "bust", username)

    @cog_ext.cog_slash(
        name="bust",
        options=[
            create_option(
                name="username",
                description="Username of account defaults to linked account.",
                option_type=3,
                required=False,
            )
        ],
    )
    async def slash_bust(self, ctx: SlashContext, username: str = None) -> None:
        """Renders a Minecraft players bust."""
        await ctx.defer()
        await self.bust(ctx, username)

    @commands.command()
    async def render(
        self,
        ctx: Union[commands.Context, SlashContext],
        render_type: str,
        username: Optional[str] = None,
    ) -> None:
        """Renders a Minecraft players skin in 6 different ways.

        You can choose from these 6 render types: face,
        front, full, head, bust & skin.
        """
        await ctx.channel.trigger_typing()
        renders = ["face", "front", "frontfull", "head", "bust", "full", "skin"]
        if render_type not in renders:
            await ctx.reply(
                _(
                    "Please supply a render type. Your "
                    "options are:\n `face`, `front`, `full`, `head`, `bust`, "
                    "`skin` \n Type: ?render <render type> <username>"
                )
            )
            return
        player_data = await self.bot.mojang_player(ctx.author, username)
        uuid = player_data["uuid"]
        username = player_data["username"]
        embed = discord.Embed(
            description=_(
                "Here is: `{username}`'s {render_type}! \n "
                "**[DOWNLOAD](https://visage.surgeplay.com/{render_type}/512/{uuid}"
                "/512/{uuid})\n[RAW](https://visage.surgeplay.com/{render_type}/512/{uuid})**"
            ).format(
                username=username,
                render_type=render_type.capitalize(),
                render_type_lower=render_type,
                uuid=uuid,
            ),
            color=self.bot.color,
        )
        embed.set_image(url=f"https://visage.surgeplay.com/{render_type}/512/{uuid}")

        await ctx.send(embed=embed)

    @cog_ext.cog_slash(
        name="render",
        options=[
            create_option(
                name="username",
                description="Username of account defaults to linked account.",
                option_type=3,
                required=False,
            )
        ],
    )
    async def slash_render(
        self, ctx: SlashContext, render_type: str, username: str = None
    ) -> None:
        """Renders a Minecraft players skin in 6 different ways."""
        await ctx.defer()
        await self.render(ctx, render_type, username)
