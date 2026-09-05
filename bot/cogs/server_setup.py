import discord
from discord import app_commands
from discord.ext import commands

from bot.config import AppSettings
from bot.db import Database
from bot.guild_resolver import resolve_guild_config


class PromptModal(discord.ui.Modal, title="Server prompt"):
    def __init__(self, db: Database, guild_id: int, current: str = ""):
        super().__init__()
        self.db = db
        self.guild_id = guild_id
        self.prompt_input = discord.ui.TextInput(
            label="Server notes for the AI",
            style=discord.TextStyle.paragraph,
            placeholder="Pricing, rules, FAQ, or anything this server should know.",
            default=current[:2000] if current else None,
            max_length=2000,
            required=True,
        )
        self.add_item(self.prompt_input)

    async def on_submit(self, interaction: discord.Interaction):
        await self.db.set_custom_prompt(self.guild_id, self.prompt_input.value.strip())
        await interaction.response.send_message("Server prompt saved.", ephemeral=True)


class ServerSetup(commands.GroupCog, name="server-setup"):
    def __init__(self, bot: commands.Bot, settings: AppSettings, db: Database):
        self.bot = bot
        self.settings = settings
        self.db = db

    @app_commands.command(name="show", description="Show bot settings for this server")
    async def show(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("Server only.", ephemeral=True)
            return

        cfg = await resolve_guild_config(self.db, interaction.guild.id)

        category = "Not set"
        if cfg.ticket_category_id:
            ch = interaction.guild.get_channel(cfg.ticket_category_id)
            category = ch.mention if ch else f"`{cfg.ticket_category_id}`"

        staff = "Not set"
        if cfg.staff_role_id:
            role = interaction.guild.get_role(cfg.staff_role_id)
            staff = role.mention if role else f"`{cfg.staff_role_id}`"

        if cfg.support_channel_ids:
            channels = []
            for cid in cfg.support_channel_ids:
                ch = interaction.guild.get_channel(cid)
                channels.append(ch.mention if ch else f"`{cid}`")
            support = ", ".join(channels)
        else:
            support = "Not set"

        prompt_preview = cfg.custom_prompt[:150] + "..." if len(cfg.custom_prompt) > 150 else (cfg.custom_prompt or "None")

        embed = discord.Embed(title="Server settings", color=discord.Color.blurple())
        embed.add_field(name="Ticket category", value=category, inline=False)
        embed.add_field(name="Staff role", value=staff, inline=False)
        embed.add_field(name="Support channels", value=support, inline=False)
        embed.add_field(name="Server prompt", value=prompt_preview, inline=False)
        embed.set_footer(text=f"Guild ID: {interaction.guild.id}")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="ticket-category", description="Set the category where tickets are created")
    @app_commands.describe(category="Ticket category (leave empty to clear)")
    async def ticket_category(
        self,
        interaction: discord.Interaction,
        category: discord.CategoryChannel | None = None,
    ):
        if not interaction.guild:
            await interaction.response.send_message("Server only.", ephemeral=True)
            return

        await self.db.set_ticket_category(interaction.guild.id, category.id if category else None)
        if category:
            await interaction.response.send_message(f"Ticket category: {category.mention}", ephemeral=True)
        else:
            await interaction.response.send_message("Ticket category cleared.", ephemeral=True)

    @app_commands.command(name="staff-role", description="Set the role pinged by Call Staff")
    @app_commands.describe(role="Staff role (leave empty to clear)")
    async def staff_role(
        self,
        interaction: discord.Interaction,
        role: discord.Role | None = None,
    ):
        if not interaction.guild:
            await interaction.response.send_message("Server only.", ephemeral=True)
            return

        await self.db.set_staff_role(interaction.guild.id, role.id if role else None)
        if role:
            await interaction.response.send_message(f"Staff role: {role.mention}", ephemeral=True)
        else:
            await interaction.response.send_message("Staff role cleared.", ephemeral=True)

    @app_commands.command(name="add-support", description="Add a channel for AI support threads")
    @app_commands.describe(channel="Support channel")
    async def add_support(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not interaction.guild:
            await interaction.response.send_message("Server only.", ephemeral=True)
            return

        added = await self.db.add_support_channel(interaction.guild.id, channel.id)
        if added:
            await interaction.response.send_message(f"Support channel added: {channel.mention}", ephemeral=True)
        else:
            await interaction.response.send_message("That channel is already registered.", ephemeral=True)

    @app_commands.command(name="remove-support", description="Remove an AI support channel")
    @app_commands.describe(channel="Support channel to remove")
    async def remove_support(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not interaction.guild:
            await interaction.response.send_message("Server only.", ephemeral=True)
            return

        removed = await self.db.remove_support_channel(interaction.guild.id, channel.id)
        if removed:
            await interaction.response.send_message(f"Support channel removed: {channel.mention}", ephemeral=True)
        else:
            await interaction.response.send_message("That channel is not registered.", ephemeral=True)

    @app_commands.command(name="set-prompt", description="Set a custom AI prompt for this server")
    async def prompt_set(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("Server only.", ephemeral=True)
            return

        cfg = await resolve_guild_config(self.db, interaction.guild.id)
        await interaction.response.send_modal(PromptModal(self.db, interaction.guild.id, cfg.custom_prompt))

    @app_commands.command(name="show-prompt", description="Show the custom AI prompt for this server")
    async def prompt_show(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("Server only.", ephemeral=True)
            return

        cfg = await resolve_guild_config(self.db, interaction.guild.id)
        if not cfg.custom_prompt:
            await interaction.response.send_message(
                "No server prompt set.\nUse `/server-setup set-prompt` to add one.",
                ephemeral=True,
            )
            return

        text = cfg.custom_prompt
        if len(text) > 1900:
            text = text[:1900] + "..."
        await interaction.response.send_message(f"```\n{text}\n```", ephemeral=True)

    @app_commands.command(name="clear-prompt", description="Clear the custom AI prompt for this server")
    async def prompt_clear(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("Server only.", ephemeral=True)
            return

        await self.db.set_custom_prompt(interaction.guild.id, "")
        await interaction.response.send_message("Server prompt cleared.", ephemeral=True)


async def setup(bot: commands.Bot):
    pass
