import asyncio
import logging
import sys

import discord
from discord.ext import commands

from bot.checks import deny_unless_developer
from bot.config import AppSettings, load_settings
from bot.cogs.bot_setup import BotSetup
from bot.cogs.dev_commands import DevCommands
from bot.cogs.server_setup import ServerSetup
from bot.cogs.support import Support
from bot.cogs.tickets import Tickets
from bot.db import Database
from bot.services.abuse_log import AbuseLogger
from bot.services.llm import LlmService
from bot.views.ticket_panel import TicketControlView, TicketPanelView
from bot.views.terms import TermsAgreementView

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("bot")


class InquiryBot(commands.Bot):
    def __init__(self, settings, db: Database, llm: LlmService):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True

        super().__init__(command_prefix=None, intents=intents)
        self.settings = settings
        self.db = db
        self.llm = llm
        self.abuse_log = AbuseLogger(self, settings.abuse_log_channel_id)
        self._commands_installed = False

    async def on_message(self, message: discord.Message):
        pass

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.type is not discord.InteractionType.application_command:
            return True
        return await deny_unless_developer(interaction, self.settings)

    async def setup_hook(self):
        await self.add_cog(Tickets(self, self.settings, self.db, self.llm))
        await self.add_cog(Support(self, self.settings, self.db, self.llm))
        await self.add_cog(ServerSetup(self, self.settings, self.db))
        await self.add_cog(BotSetup(self, self.settings, self.db))
        await self.add_cog(DevCommands(self, self.settings))

        self.add_view(TicketPanelView())
        self.add_view(TicketControlView())
        self.add_view(TermsAgreementView())

    async def _install_guild_commands(self, guild: discord.Guild):
        self.tree.clear_commands(guild=guild)
        self.tree.copy_global_to(guild=guild)
        synced = await self.tree.sync(guild=guild)
        log.info("서버 명령 등록 [%s]: %d개", guild.name, len(synced))
        for cmd in synced:
            if isinstance(cmd, discord.app_commands.Group):
                subs = ", ".join(c.name for c in cmd.commands)
                log.info("  /%s → %s", cmd.name, subs)
            else:
                log.info("  /%s", cmd.name)

    async def _remove_global_commands(self):
        await self.http.bulk_upsert_global_commands(self.application_id, payload=[])
        log.info("전역 명령 제거 완료 (서버 전용만 사용)")

    async def _install_commands(self):
        if not self.guilds:
            log.warning("연결된 서버가 없어 명령 등록을 건너뜁니다.")
            return

        for guild in self.guilds:
            try:
                await self._install_guild_commands(guild)
            except discord.HTTPException as e:
                log.error("서버 명령 등록 실패 [%s]: %s", guild.name, e)

        try:
            await self._remove_global_commands()
        except discord.HTTPException as e:
            log.error("전역 명령 제거 실패: %s", e)

    async def on_ready(self):
        log.info("%s 로그인 완료 (guilds=%d)", self.user, len(self.guilds))
        if self._commands_installed:
            return
        self._commands_installed = True
        await self._install_commands()

    async def on_guild_join(self, guild: discord.Guild):
        try:
            await self._install_guild_commands(guild)
        except discord.HTTPException as e:
            log.error("신규 서버 명령 등록 실패 [%s]: %s", guild.name, e)


async def main():
    settings = load_settings()

    if not settings.discord_token:
        log.error("DISCORD_TOKEN이 설정되지 않았습니다. .env 파일을 확인하세요.")
        sys.exit(1)
    if not settings.developer_ids:
        log.error("DEVELOPER_IDS가 설정되지 않았습니다. .env에 디스코드 유저 ID를 추가하세요.")
        sys.exit(1)

    db = Database(settings.db_path)
    await db.connect()

    llm = LlmService(settings, db)
    if not await llm.health_check():
        log.error(
            "Ollama에 연결할 수 없습니다. Ollama를 실행한 뒤 모델을 받아주세요:\n"
            "  ollama pull %s\n"
            "  ollama serve",
            settings.default_ollama_model,
        )
        sys.exit(1)

    runtime = await db.get_llm_runtime(llm._defaults())
    log.info("로컬 LLM 준비 완료 (model=%s)", runtime.model)

    bot = InquiryBot(settings, db, llm)
    llm.abuse_log = bot.abuse_log

    try:
        await bot.start(settings.discord_token)
    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
