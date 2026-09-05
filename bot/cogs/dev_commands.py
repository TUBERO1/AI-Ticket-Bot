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
            title="명령어",
            description=(
                "`DEVELOPER_IDS`에 등록된 사람만 쓸 수 있습니다.\n"
                "안 보이면 `/서버설정` 또는 `/봇설정`을 직접 쳐 보세요."
            ),
            color=discord.Color.blurple(),
        )
        embed.add_field(
            name="티켓",
            value="`/티켓패널` — 문의 패널 배포",
            inline=False,
        )
        embed.add_field(
            name="서버설정",
            value=(
                "`/서버설정 보기`\n"
                "`/서버설정 티켓카테고리`\n"
                "`/서버설정 관리자역할`\n"
                "`/서버설정 문의채널등록` / `문의채널해제`\n"
                "`/서버설정 프롬프트설정` / `프롬프트보기` / `프롬프트삭제`"
            ),
            inline=False,
        )
        embed.add_field(
            name="봇설정",
            value="`/봇설정 보기` · `모델` · `주소` · `최대토큰` · `온도`",
            inline=False,
        )
        embed.add_field(name="도움말", value="`/명령어`", inline=False)
        embed.set_footer(text=f"개발자 {len(self.settings.developer_ids)}명")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    pass
