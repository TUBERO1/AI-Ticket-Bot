import discord
from discord import app_commands
from discord.ext import commands

from bot.config import AppSettings


class DevCommands(commands.Cog):
    def __init__(self, bot: commands.Bot, settings: AppSettings):
        self.bot = bot
        self.settings = settings

    @app_commands.command(name="명령어", description="봇 명령어 전체 목록을 표시합니다")
    async def command_list(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Lumentia 봇 명령어",
            description=(
                "아래 명령은 **DEVELOPER_IDS**에 등록된 개발자만 사용할 수 있습니다.\n"
                "명령이 안 보이면 `/서버설정` 또는 `/봇설정`을 **직접 입력**해 보세요. (그룹 명령)"
            ),
            color=discord.Color.blurple(),
        )
        embed.add_field(
            name="티켓",
            value="`/티켓패널` — 문의 티켓 패널 배포",
            inline=False,
        )
        embed.add_field(
            name="서버설정 (서버마다 따로)",
            value=(
                "`/서버설정 보기` — 설정 확인\n"
                "`/서버설정 모드` — Lumentia / RFIVEM 모드\n"
                "`/서버설정 티켓카테고리` — 티켓 카테고리\n"
                "`/서버설정 관리자역할` — 관리자 역할\n"
                "`/서버설정 문의채널등록` / `문의채널해제`\n"
                "`/서버설정 프롬프트설정` — 서버 AI 프롬프트\n"
                "`/서버설정 프롬프트보기` / `프롬프트삭제`"
            ),
            inline=False,
        )
        embed.add_field(
            name="봇설정 (전역 LLM)",
            value=(
                "`/봇설정 보기` — Ollama 설정 확인\n"
                "`/봇설정 모델` / `주소` / `최대토큰` / `온도`"
            ),
            inline=False,
        )
        embed.add_field(name="도움말", value="`/명령어` — 이 목록", inline=False)
        embed.set_footer(text=f"등록된 개발자 {len(self.settings.developer_ids)}명")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    pass
