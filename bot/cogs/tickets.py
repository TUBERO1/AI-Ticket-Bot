import discord
from discord import app_commands
from discord.ext import commands

from bot.config import AppSettings
from bot.db import Database
from bot.guild_resolver import resolve_guild_config
from bot.services.abuse_log import AbuseContext
from bot.services.llm import LlmService
from bot.utils import Debounce, ensure_terms_before_ai, send_ai_reply
from bot.views.ticket_panel import TicketCloseConfirmView, TicketControlView, TicketPanelView


class Tickets(commands.Cog):
    def __init__(self, bot: commands.Bot, settings: AppSettings, db: Database, llm: LlmService):
        self.bot = bot
        self.settings = settings
        self.db = db
        self.llm = llm
        self.debounce = Debounce(settings.debounce_seconds)

    def _staff_overwrites(self, guild: discord.Guild, user: discord.Member, staff_role_id: int | None) -> dict:
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
            ),
            guild.me: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                manage_channels=True,
                read_message_history=True,
            ),
        }
        if staff_role_id:
            staff_role = guild.get_role(staff_role_id)
            if staff_role:
                overwrites[staff_role] = discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                )
        return overwrites

    def _resolve_category(self, guild: discord.Guild, category_id: int | None) -> discord.CategoryChannel | None:
        if not category_id:
            return None
        ch = guild.get_channel(category_id)
        if isinstance(ch, discord.CategoryChannel):
            return ch
        return None

    @app_commands.command(name="티켓패널", description="문의 티켓 패널을 이 채널에 배포합니다")
    async def deploy_panel(self, interaction: discord.Interaction):
        if not interaction.guild or not interaction.channel:
            await interaction.response.send_message("서버 채널에서만 사용할 수 있습니다.", ephemeral=True)
            return

        embed = discord.Embed(
            title="📩 1:1 문의",
            description=(
                "아래 **문의하기**를 누르면 개인 문의 채널이 만들어집니다.\n"
                "AI가 먼저 답하고, 필요하면 **관리자 호출**도 됩니다."
            ),
            color=discord.Color.blurple(),
        )
        await interaction.response.send_message("티켓 패널을 배포했습니다.", ephemeral=True)
        await interaction.channel.send(embed=embed, view=TicketPanelView())

    async def open_ticket(self, interaction: discord.Interaction):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            if not interaction.response.is_done():
                await interaction.response.send_message("서버에서만 이용할 수 있습니다.", ephemeral=True)
            return

        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)

        guild_cfg = await resolve_guild_config(self.db, interaction.guild.id)

        existing = await self.db.get_open_ticket_by_user(interaction.guild.id, interaction.user.id)
        if existing:
            channel = interaction.guild.get_channel(existing["channel_id"])
            if channel:
                await interaction.followup.send(
                    f"이미 열린 티켓이 있습니다: {channel.mention}",
                    ephemeral=True,
                )
                return
            await self.db.close_stale_ticket(existing["channel_id"])

        category = self._resolve_category(interaction.guild, guild_cfg.ticket_category_id)
        safe_name = "".join(c for c in interaction.user.name[:20] if c.isalnum() or c in "-_") or "user"
        channel_name = f"티켓-{safe_name}"

        try:
            channel = await interaction.guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=self._staff_overwrites(interaction.guild, interaction.user, guild_cfg.staff_role_id),
                reason=f"티켓 생성: {interaction.user}",
            )
        except discord.Forbidden:
            await interaction.followup.send(
                "티켓 채널을 만들 권한이 없습니다. 봇 권한과 카테고리 설정을 확인해 주세요.",
                ephemeral=True,
            )
            return
        except discord.HTTPException as e:
            await interaction.followup.send(f"티켓 생성 실패: {e.text}", ephemeral=True)
            return

        ticket_id = await self.db.create_ticket(channel.id, interaction.guild.id, interaction.user.id)
        welcome = (
            f"{interaction.user.mention} 님, 문의 채널이 열렸습니다.\n\n"
            "궁금한 내용을 메시지로 남겨 주시면 AI가 도와드립니다.\n"
            "해결이 어려우면 **관리자 호출** 버튼을 눌러 주세요."
        )
        await channel.send(welcome, view=TicketControlView())
        await self.db.add_message(
            "assistant",
            self.llm.welcome_message(),
            ticket_id=ticket_id,
        )
        await interaction.followup.send(f"티켓이 생성되었습니다: {channel.mention}", ephemeral=True)

    async def call_staff(self, interaction: discord.Interaction):
        if not interaction.guild or not interaction.channel:
            return

        ticket = await self.db.get_ticket_by_channel(interaction.channel.id)
        if not ticket or ticket["status"] != "open":
            await interaction.response.send_message("열린 티켓 채널이 아닙니다.", ephemeral=True)
            return

        guild_cfg = await resolve_guild_config(self.db, interaction.guild.id)
        mention = ""
        if guild_cfg.staff_role_id:
            mention = f"<@&{guild_cfg.staff_role_id}> "

        await interaction.response.send_message(
            f"{mention}관리자 호출 요청이 접수되었습니다. 잠시만 기다려 주세요.",
            allowed_mentions=discord.AllowedMentions(roles=True),
        )

    async def request_close(self, interaction: discord.Interaction):
        ticket = await self.db.get_ticket_by_channel(interaction.channel.id)
        if not ticket or ticket["status"] != "open":
            await interaction.response.send_message("열린 티켓 채널이 아닙니다.", ephemeral=True)
            return

        guild_cfg = await resolve_guild_config(self.db, interaction.guild.id)
        is_owner = interaction.user.id == ticket["user_id"]
        is_staff = False
        if guild_cfg.staff_role_id and isinstance(interaction.user, discord.Member):
            is_staff = any(r.id == guild_cfg.staff_role_id for r in interaction.user.roles)

        if not is_owner and not is_staff and not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("티켓을 종료할 권한이 없습니다.", ephemeral=True)
            return

        await interaction.response.send_message(
            "정말 이 티켓을 종료할까요? 채널이 삭제됩니다.",
            view=TicketCloseConfirmView(),
        )

    async def confirm_close(self, interaction: discord.Interaction):
        if not isinstance(interaction.channel, discord.TextChannel):
            await interaction.response.send_message("티켓 채널에서만 종료할 수 있습니다.", ephemeral=True)
            return

        ticket = await self.db.get_ticket_by_channel(interaction.channel.id)
        if not ticket:
            await interaction.response.send_message("티켓 정보를 찾을 수 없습니다.", ephemeral=True)
            return

        await self.db.close_ticket(interaction.channel.id)
        await interaction.response.send_message("티켓을 종료합니다. 채널이 곧 삭제됩니다.", ephemeral=True)
        await interaction.channel.delete(reason=f"티켓 종료: {interaction.user}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        ticket = await self.db.get_ticket_by_channel(message.channel.id)
        if not ticket or ticket["status"] != "open":
            return

        if message.author.id != ticket["user_id"]:
            return

        if not message.content or not message.content.strip():
            return

        guild_cfg = await resolve_guild_config(self.db, message.guild.id)
        await self.debounce.wait(message.channel.id)

        if not await ensure_terms_before_ai(
            message,
            self.db,
            guild_cfg.custom_prompt,
            ticket_id=ticket["id"],
            thread_id=None,
        ):
            return

        try:
            await send_ai_reply(
                message.channel,
                self.db,
                self.llm,
                self.settings,
                message.content.strip(),
                ticket_id=ticket["id"],
                custom_prompt=guild_cfg.custom_prompt,
                abuse_ctx=AbuseContext.from_message(message),
            )
        except discord.HTTPException:
            await message.channel.send("응답 전송에 실패했습니다. 다시 시도해 주세요.")


async def setup(bot: commands.Bot):
    pass
