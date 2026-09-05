import discord
from discord import app_commands
from discord.ext import commands

from bot.config import AppSettings


class DevCommands(commands.Cog):
    def __init__(self, bot: commands.Bot, settings: AppSettings):
        self.bot = bot
        self.settings = settings

    @app_commands.command(name="commands", description="List all bot commands")
    async def command_list(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Commands",
            description=(
                "Only users listed in `DEVELOPER_IDS` can use these.\n"
                "If you don't see them, type `/server-setup` or `/bot-setup` directly."
            ),
            color=discord.Color.blurple(),
        )
        embed.add_field(
            name="Tickets",
            value="`/ticket-panel` — post the ticket panel",
            inline=False,
        )
        embed.add_field(
            name="Server setup",
            value=(
                "`/server-setup show`\n"
                "`/server-setup ticket-category`\n"
                "`/server-setup staff-role`\n"
                "`/server-setup add-support` / `remove-support`\n"
                "`/server-setup set-prompt` / `show-prompt` / `clear-prompt`"
            ),
            inline=False,
        )
        embed.add_field(
            name="Bot setup",
            value="`/bot-setup show` · `model` · `url` · `max-tokens` · `temperature`",
            inline=False,
        )
        embed.add_field(name="Help", value="`/commands`", inline=False)
        embed.set_footer(text=f"{len(self.settings.developer_ids)} developer(s)")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    pass
