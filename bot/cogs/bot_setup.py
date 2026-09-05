import discord
from discord import app_commands
from discord.ext import commands

from bot.config import AppSettings
from bot.db import Database
from bot.guild_config import LlmRuntimeConfig


class BotSetup(commands.GroupCog, name="봇설정"):
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

    @app_commands.command(name="보기", description="Ollama / LLM 설정을 확인합니다")
    async def show(self, interaction: discord.Interaction):
        runtime = await self.db.get_llm_runtime(self._defaults())
        embed = discord.Embed(title="LLM 설정", color=discord.Color.green())
        embed.add_field(name="Ollama 주소", value=runtime.base_url, inline=False)
        embed.add_field(name="모델", value=runtime.model, inline=True)
        embed.add_field(name="최대 토큰", value=str(runtime.max_tokens), inline=True)
        embed.add_field(name="온도", value=str(runtime.temperature), inline=True)
        embed.set_footer(text="미설정 항목은 .env 기본값 사용")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="모델", description="Ollama 모델명을 설정합니다")
    @app_commands.describe(model="예: exaone3.5:7.8b")
    async def model(self, interaction: discord.Interaction, model: str):
        await self.db.set_bot_setting("ollama_model", model.strip())
        await interaction.response.send_message(f"모델: `{model}`", ephemeral=True)

    @app_commands.command(name="주소", description="Ollama API 주소를 설정합니다")
    @app_commands.describe(url="예: http://localhost:11434/v1")
    async def base_url(self, interaction: discord.Interaction, url: str):
        fixed = url.strip()
        if not fixed.endswith("/"):
            fixed += "/"
        await self.db.set_bot_setting("ollama_base_url", fixed)
        await interaction.response.send_message(f"Ollama 주소: `{fixed}`", ephemeral=True)

    @app_commands.command(name="최대토큰", description="AI 응답 최대 토큰 수")
    @app_commands.describe(tokens="예: 2048")
    async def max_tokens(self, interaction: discord.Interaction, tokens: app_commands.Range[int, 256, 8192]):
        await self.db.set_bot_setting("ollama_max_tokens", str(tokens))
        await interaction.response.send_message(f"최대 토큰: `{tokens}`", ephemeral=True)

    @app_commands.command(name="온도", description="AI 응답 온도 (0.0~1.0)")
    @app_commands.describe(value="예: 0.7")
    async def temperature(self, interaction: discord.Interaction, value: app_commands.Range[float, 0.0, 1.0]):
        await self.db.set_bot_setting("ollama_temperature", str(value))
        await interaction.response.send_message(f"온도: `{value}`", ephemeral=True)


async def setup(bot: commands.Bot):
    pass
