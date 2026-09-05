import discord
from discord import app_commands
from discord.ext import commands

from bot.config import AppSettings
from bot.db import Database
from bot.guild_config import LlmRuntimeConfig


class BotSetup(commands.GroupCog, name="bot-setup"):
    def __init__(self, bot: commands.Bot, settings: AppSettings, db: Database):
        self.bot = bot
        self.settings = settings
        self.db = db

    def _defaults(self) -> LlmRuntimeConfig:
        return LlmRuntimeConfig(
            base_url=self.settings.default_ollama_base_url,
            model=self.settings.default_ollama_model,
            max_tokens=self.settings.default_ollama_max_tokens,
            temperature=self.settings.default_ollama_temperature,
        )

    @app_commands.command(name="show", description="Show Ollama / LLM settings")
    async def show(self, interaction: discord.Interaction):
        runtime = await self.db.get_llm_runtime(self._defaults())
        embed = discord.Embed(title="LLM settings", color=discord.Color.green())
        embed.add_field(name="Ollama URL", value=runtime.base_url, inline=False)
        embed.add_field(name="Model", value=runtime.model, inline=True)
        embed.add_field(name="Max tokens", value=str(runtime.max_tokens), inline=True)
        embed.add_field(name="Temperature", value=str(runtime.temperature), inline=True)
        embed.set_footer(text="Unset values fall back to .env defaults")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="model", description="Set the Ollama model name")
    @app_commands.describe(model="Example: exaone3.5:7.8b")
    async def model(self, interaction: discord.Interaction, model: str):
        await self.db.set_bot_setting("ollama_model", model.strip())
        await interaction.response.send_message(f"Model: `{model}`", ephemeral=True)

    @app_commands.command(name="url", description="Set the Ollama API base URL")
    @app_commands.describe(url="Example: http://localhost:11434/v1")
    async def base_url(self, interaction: discord.Interaction, url: str):
        fixed = url.strip()
        if not fixed.endswith("/"):
            fixed += "/"
        await self.db.set_bot_setting("ollama_base_url", fixed)
        await interaction.response.send_message(f"Ollama URL: `{fixed}`", ephemeral=True)

    @app_commands.command(name="max-tokens", description="Max tokens for AI replies")
    @app_commands.describe(tokens="Example: 2048")
    async def max_tokens(self, interaction: discord.Interaction, tokens: app_commands.Range[int, 256, 8192]):
        await self.db.set_bot_setting("ollama_max_tokens", str(tokens))
        await interaction.response.send_message(f"Max tokens: `{tokens}`", ephemeral=True)

    @app_commands.command(name="temperature", description="AI temperature (0.0~1.0)")
    @app_commands.describe(value="Example: 0.7")
    async def temperature(self, interaction: discord.Interaction, value: app_commands.Range[float, 0.0, 1.0]):
        await self.db.set_bot_setting("ollama_temperature", str(value))
        await interaction.response.send_message(f"Temperature: `{value}`", ephemeral=True)


async def setup(bot: commands.Bot):
    pass
