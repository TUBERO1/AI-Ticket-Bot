import asyncio
from collections import defaultdict

import discord
from discord.ext import commands

from bot.config import AppSettings
from bot.db import Database
from bot.services.abuse_log import AbuseContext
from bot.services.llm import LlmService
from bot.services.output import SAFE_MENTIONS, split_reply_for_send
from bot.services.terms import TERMS_VERSION
from bot.views.terms import TermsAgreementView


class Debounce:
    def __init__(self, seconds: float):
        self.seconds = seconds
        self._locks: dict[int, asyncio.Lock] = defaultdict(asyncio.Lock)
        self._last_call: dict[int, float] = {}

    async def wait(self, key: int):
        lock = self._locks[key]
        async with lock:
            loop = asyncio.get_event_loop()
            now = loop.time()
            last = self._last_call.get(key, 0)
            delta = now - last
            if delta < self.seconds:
                await asyncio.sleep(self.seconds - delta)
            self._last_call[key] = loop.time()


async def send_ai_reply(
    channel: discord.abc.Messageable,
    db: Database,
    llm: LlmService,
    settings: AppSettings,
    user_content: str,
    ticket_id: int | None = None,
    thread_id: int | None = None,
    custom_prompt: str = "",
    abuse_ctx: AbuseContext | None = None,
):
    await db.add_message("user", user_content, ticket_id=ticket_id, thread_id=thread_id)
    history = await db.get_messages(
        ticket_id=ticket_id,
        thread_id=thread_id,
        limit=settings.history_limit,
    )

    async with channel.typing():
        reply = await llm.chat(
            history,
            custom_prompt=custom_prompt,
            abuse_ctx=abuse_ctx,
        )

    await db.add_message("assistant", reply, ticket_id=ticket_id, thread_id=thread_id)
    body, footer = split_reply_for_send(reply)
    if body:
        await channel.send(body, allowed_mentions=SAFE_MENTIONS)
    if footer:
        await channel.send(footer, allowed_mentions=SAFE_MENTIONS, suppress_embeds=True)


async def process_pending_consult(bot: commands.Bot, db: Database, user_id: int) -> bool:
    pending = await db.get_pending_consult(user_id)
    if not pending:
        return False

    guild = bot.get_guild(pending["guild_id"])
    if not guild:
        await db.clear_pending_consult(user_id)
        return False

    channel = guild.get_channel(pending["channel_id"])
    if not channel:
        await db.clear_pending_consult(user_id)
        return False

    settings = bot.settings
    llm = bot.llm

    try:
        ctx = AbuseContext(
            user_id=user_id,
            user_name=str(user_id),
            guild_id=pending["guild_id"],
            guild_name=guild.name,
            channel_id=pending["channel_id"],
            channel_name=getattr(channel, "name", str(pending["channel_id"])),
        )
        member = guild.get_member(user_id)
        if member:
            ctx.user_name = str(member)

        await send_ai_reply(
            channel,
            db,
            llm,
            settings,
            pending["content"],
            ticket_id=pending["ticket_id"],
            thread_id=pending["thread_id"],
            custom_prompt=pending["custom_prompt"] or "",
            abuse_ctx=ctx,
        )
    except discord.HTTPException:
        await channel.send("Failed to send the reply. Please try again.")
        return False
    finally:
        await db.clear_pending_consult(user_id)

    return True


async def ensure_terms_before_ai(
    message: discord.Message,
    db: Database,
    custom_prompt: str,
    ticket_id: int | None,
    thread_id: int | None,
    reply_channel: discord.abc.Messageable | None = None,
) -> bool:
    if await db.has_terms_agreed(message.author.id, TERMS_VERSION):
        return True

    target = reply_channel or message.channel
    target_id = getattr(target, "id", message.channel.id)

    await db.set_pending_consult(
        user_id=message.author.id,
        guild_id=message.guild.id,
        channel_id=target_id,
        content=message.content.strip(),
        server_mode="default",
        thread_id=thread_id,
        ticket_id=ticket_id,
        custom_prompt=custom_prompt,
    )

    prompt = (
        f"{message.author.mention} To use AI support, please **agree to the terms**.\n"
        "**View Terms** is only visible to you, and **Agree** is only needed once."
    )
    await target.send(prompt, view=TermsAgreementView(), allowed_mentions=SAFE_MENTIONS)
    return False
