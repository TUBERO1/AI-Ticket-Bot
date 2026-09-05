import discord
from discord.ext import commands

from bot.config import AppSettings
from bot.db import Database
from bot.guild_resolver import resolve_guild_config
from bot.services.abuse_log import AbuseContext
from bot.services.llm import LlmService
from bot.utils import Debounce, ensure_terms_before_ai, send_ai_reply


class Support(commands.Cog):
    def __init__(self, bot: commands.Bot, settings: AppSettings, db: Database, llm: LlmService):
        self.bot = bot
        self.settings = settings
        self.db = db
        self.llm = llm
        self.debounce = Debounce(settings.debounce_seconds)

    def _in_support_area(self, channel: discord.abc.GuildChannel, support_ids: list[int]) -> bool:
        if isinstance(channel, discord.Thread):
            return channel.parent_id in support_ids
        return channel.id in support_ids

    def _display_name(self, user: discord.User | discord.Member) -> str:
        if isinstance(user, discord.Member):
            return user.display_name
        return user.name

    def _safe_name(self, user: discord.User | discord.Member) -> str:
        raw = self._display_name(user).strip()
        safe = "".join(c for c in raw[:16] if c.isalnum() or c in "-_ ") or "user"
        return safe.strip() or "user"

    def _thread_name(self, user: discord.User | discord.Member) -> str:
        return f"inquiry-{self._safe_name(user)}-{user.id}"

    def _is_bot(self, user_id: int | None) -> bool:
        return bool(user_id and self.bot.user and user_id == self.bot.user.id)

    async def _owner_from_intro(self, thread: discord.Thread) -> int | None:
        try:
            async for msg in thread.history(limit=10, oldest_first=True):
                if not msg.author.bot:
                    continue
                if "support thread" not in msg.content.lower():
                    continue
                for user in msg.mentions:
                    if not user.bot:
                        return user.id
        except discord.HTTPException:
            pass
        return None

    async def _owner_from_starter(self, thread: discord.Thread) -> int | None:
        try:
            starter = thread.starter_message
            if starter is None:
                starter = await thread.fetch_starter_message()
            if starter and not starter.author.bot:
                return starter.author.id
        except discord.HTTPException:
            pass
        return None

    async def _save_owner(self, thread: discord.Thread, user_id: int):
        if self._is_bot(user_id):
            return
        await self.db.set_support_thread_owner(thread.id, thread.guild.id, user_id)

    async def _resolve_thread_owner(self, thread: discord.Thread) -> int | None:
        stored = await self.db.get_support_thread_owner(thread.id)
        if stored and not self._is_bot(stored):
            return stored
        if stored and self._is_bot(stored):
            await self.db.clear_support_thread_owner(thread.id)

        intro_owner = await self._owner_from_intro(thread)
        if intro_owner:
            await self._save_owner(thread, intro_owner)
            return intro_owner

        starter_owner = await self._owner_from_starter(thread)
        if starter_owner:
            await self._save_owner(thread, starter_owner)
            return starter_owner

        owner_id = thread.owner_id
        if not self._is_bot(owner_id):
            if owner_id:
                await self._save_owner(thread, owner_id)
                return owner_id

        try:
            fresh = await thread.guild.fetch_channel(thread.id)
            if isinstance(fresh, discord.Thread):
                fetched_owner = fresh.owner_id
                if not self._is_bot(fetched_owner) and fetched_owner:
                    await self._save_owner(fresh, fetched_owner)
                    return fetched_owner
        except discord.HTTPException:
            pass

        return None

    async def _owns_thread(self, thread: discord.Thread, user: discord.User | discord.Member) -> bool:
        owner_id = await self._resolve_thread_owner(thread)
        if owner_id == user.id:
            return True

        if str(user.id) in thread.name:
            await self._save_owner(thread, user.id)
            return True

        return False

    async def _create_thread(self, message: discord.Message) -> discord.Thread:
        thread = await message.create_thread(
            name=self._thread_name(message.author),
            auto_archive_duration=1440,
            reason=f"Support thread for {message.author}",
        )

        await self._save_owner(thread, message.author.id)
        intro = (
            f"{message.author.mention}, this is your support thread.\n"
            "Only you should use this thread. Continue the conversation here."
        )
        await thread.send(intro)
        return thread

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        guild_cfg = await resolve_guild_config(self.db, message.guild.id)
        if not guild_cfg.support_channel_ids:
            return

        if not self._in_support_area(message.channel, guild_cfg.support_channel_ids):
            return

        if not message.content or not message.content.strip():
            return

        if isinstance(message.channel, discord.Thread):
            if not await self._owns_thread(message.channel, message.author):
                try:
                    await message.reply(
                        "This is someone else's support thread. Post in the channel to open a new one.",
                        mention_author=False,
                    )
                except discord.HTTPException:
                    pass
                return
            thread = message.channel
        else:
            if not isinstance(message.channel, discord.TextChannel):
                return
            try:
                thread = await self._create_thread(message)
            except (discord.Forbidden, discord.HTTPException):
                await message.channel.send(
                    f"{message.author.mention} I couldn't create a thread. Check bot permissions.",
                    delete_after=15,
                )
                return

        await self.debounce.wait(thread.id)

        if not await ensure_terms_before_ai(
            message,
            self.db,
            guild_cfg.custom_prompt,
            ticket_id=None,
            thread_id=thread.id,
            reply_channel=thread,
        ):
            return

        try:
            await send_ai_reply(
                thread,
                self.db,
                self.llm,
                self.settings,
                message.content.strip(),
                thread_id=thread.id,
                custom_prompt=guild_cfg.custom_prompt,
                abuse_ctx=AbuseContext.from_message(message),
            )
        except discord.HTTPException:
            await thread.send("Failed to send the reply. Please try again.")


async def setup(bot: commands.Bot):
    pass
