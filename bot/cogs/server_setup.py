import discord
from discord import app_commands
from discord.ext import commands

from bot.config import AppSettings
from bot.db import Database
from bot.guild_config import MODE_LUMENTIA, MODE_RFIVEM
from bot.guild_resolver import resolve_guild_config


class PromptModal(discord.ui.Modal, title="서버 프롬프트 설정"):
    def __init__(self, db: Database, guild_id: int, current: str = ""):
        super().__init__()
        self.db = db
        self.guild_id = guild_id
        self.prompt_input = discord.ui.TextInput(
            label="서버 전용 AI 안내",
            style=discord.TextStyle.paragraph,
            placeholder="이 서버만의 가격, 정책, 서비스 설명 등을 적으세요.",
            default=current[:2000] if current else None,
            max_length=2000,
            required=True,
        )
        self.add_item(self.prompt_input)

    async def on_submit(self, interaction: discord.Interaction):
        await self.db.set_custom_prompt(self.guild_id, self.prompt_input.value.strip())
        await interaction.response.send_message("서버 프롬프트가 저장되었습니다.", ephemeral=True)


class ServerSetup(commands.GroupCog, name="서버설정"):
    def __init__(self, bot: commands.Bot, settings: AppSettings, db: Database):
        self.bot = bot
        self.settings = settings
        self.db = db

    @app_commands.command(name="보기", description="이 서버의 봇 설정을 확인합니다")
    async def show(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("서버에서만 사용할 수 있습니다.", ephemeral=True)
            return

        cfg = await resolve_guild_config(self.db, interaction.guild.id)

        category = "미설정"
        if cfg.ticket_category_id:
            ch = interaction.guild.get_channel(cfg.ticket_category_id)
            category = ch.mention if ch else f"`{cfg.ticket_category_id}`"

        staff = "미설정"
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
            support = "미설정"

        prompt_preview = cfg.custom_prompt[:150] + "..." if len(cfg.custom_prompt) > 150 else (cfg.custom_prompt or "없음")

        mode_label = "RFIVEM (법률·RP 판별)" if cfg.server_mode == MODE_RFIVEM else "Lumentia (외주 문의)"

        embed = discord.Embed(title="서버 설정", color=discord.Color.blurple())
        embed.add_field(name="서버 모드", value=mode_label, inline=False)
        embed.add_field(name="티켓 카테고리", value=category, inline=False)
        embed.add_field(name="관리자 역할", value=staff, inline=False)
        embed.add_field(name="문의 채널", value=support, inline=False)
        embed.add_field(name="서버 프롬프트", value=prompt_preview, inline=False)
        embed.set_footer(text=f"서버 ID: {interaction.guild.id}")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="모드", description="서버 AI 모드를 설정합니다 (Lumentia / RFIVEM)")
    @app_commands.describe(mode="lumentia=외주 문의, rfivem=법률·RP 판별")
    @app_commands.choices(
        mode=[
            app_commands.Choice(name="Lumentia (외주 문의)", value=MODE_LUMENTIA),
            app_commands.Choice(name="RFIVEM (법률·RP 판별)", value=MODE_RFIVEM),
        ]
    )
    async def server_mode(self, interaction: discord.Interaction, mode: app_commands.Choice[str]):
        if not interaction.guild:
            await interaction.response.send_message("서버에서만 사용할 수 있습니다.", ephemeral=True)
            return

        await self.db.set_server_mode(interaction.guild.id, mode.value)
        if mode.value == MODE_RFIVEM:
            label = "RFIVEM (법률·RP 판별)"
        else:
            label = "Lumentia (외주 문의)"
        await interaction.response.send_message(f"서버 모드: **{label}**", ephemeral=True)

    @app_commands.command(name="티켓카테고리", description="티켓이 생성될 카테고리를 설정합니다")
    @app_commands.describe(category="티켓 채널 카테고리 (비우면 해제)")
    async def ticket_category(
        self,
        interaction: discord.Interaction,
        category: discord.CategoryChannel | None = None,
    ):
        if not interaction.guild:
            await interaction.response.send_message("서버에서만 사용할 수 있습니다.", ephemeral=True)
            return

        await self.db.set_ticket_category(interaction.guild.id, category.id if category else None)
        if category:
            await interaction.response.send_message(f"티켓 카테고리: {category.mention}", ephemeral=True)
        else:
            await interaction.response.send_message("티켓 카테고리 설정이 해제되었습니다.", ephemeral=True)

    @app_commands.command(name="관리자역할", description="관리자 호출 시 멘션할 역할을 설정합니다")
    @app_commands.describe(role="관리자 역할 (비우면 해제)")
    async def staff_role(
        self,
        interaction: discord.Interaction,
        role: discord.Role | None = None,
    ):
        if not interaction.guild:
            await interaction.response.send_message("서버에서만 사용할 수 있습니다.", ephemeral=True)
            return

        await self.db.set_staff_role(interaction.guild.id, role.id if role else None)
        if role:
            await interaction.response.send_message(f"관리자 역할: {role.mention}", ephemeral=True)
        else:
            await interaction.response.send_message("관리자 역할 설정이 해제되었습니다.", ephemeral=True)

    @app_commands.command(name="문의채널등록", description="AI 자동응답 문의 채널을 추가합니다")
    @app_commands.describe(channel="문의 채널")
    async def add_support(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not interaction.guild:
            await interaction.response.send_message("서버에서만 사용할 수 있습니다.", ephemeral=True)
            return

        added = await self.db.add_support_channel(interaction.guild.id, channel.id)
        if added:
            await interaction.response.send_message(f"문의 채널 등록: {channel.mention}", ephemeral=True)
        else:
            await interaction.response.send_message("이미 등록된 채널입니다.", ephemeral=True)

    @app_commands.command(name="문의채널해제", description="AI 자동응답 문의 채널을 제거합니다")
    @app_commands.describe(channel="해제할 문의 채널")
    async def remove_support(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not interaction.guild:
            await interaction.response.send_message("서버에서만 사용할 수 있습니다.", ephemeral=True)
            return

        removed = await self.db.remove_support_channel(interaction.guild.id, channel.id)
        if removed:
            await interaction.response.send_message(f"문의 채널 해제: {channel.mention}", ephemeral=True)
        else:
            await interaction.response.send_message("등록되지 않은 채널입니다.", ephemeral=True)

    @app_commands.command(name="프롬프트설정", description="이 서버 전용 AI 프롬프트를 설정합니다")
    async def prompt_set(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("서버에서만 사용할 수 있습니다.", ephemeral=True)
            return

        cfg = await resolve_guild_config(self.db, interaction.guild.id)
        await interaction.response.send_modal(PromptModal(self.db, interaction.guild.id, cfg.custom_prompt))

    @app_commands.command(name="프롬프트보기", description="이 서버에 설정된 AI 프롬프트를 확인합니다")
    async def prompt_show(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("서버에서만 사용할 수 있습니다.", ephemeral=True)
            return

        cfg = await resolve_guild_config(self.db, interaction.guild.id)
        if not cfg.custom_prompt:
            await interaction.response.send_message(
                "설정된 서버 프롬프트가 없습니다.\n"
                "`/서버설정 프롬프트설정`으로 추가하세요.",
                ephemeral=True,
            )
            return

        text = cfg.custom_prompt
        if len(text) > 1900:
            text = text[:1900] + "..."
        await interaction.response.send_message(f"```\n{text}\n```", ephemeral=True)

    @app_commands.command(name="프롬프트삭제", description="서버 전용 AI 프롬프트를 삭제합니다")
    async def prompt_clear(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("서버에서만 사용할 수 있습니다.", ephemeral=True)
            return

        await self.db.set_custom_prompt(interaction.guild.id, "")
        await interaction.response.send_message("서버 프롬프트가 삭제되었습니다.", ephemeral=True)


async def setup(bot: commands.Bot):
    pass
