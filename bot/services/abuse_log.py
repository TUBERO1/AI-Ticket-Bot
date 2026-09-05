from dataclasses import dataclass
from datetime import datetime, timezone
import logging

import discord

log = logging.getLogger("bot.abuse")

EVENT_META = {
    "injection": ("Prompt injection", discord.Color.red()),
    "out_of_scope": ("Out of scope", discord.Color.orange()),
    "unsafe_output": ("Unsafe output blocked", discord.Color.red()),
    "spam_repeat": ("Spam / repeat", discord.Color.dark_red()),
}


@dataclass
class AbuseContext:
    user_id: int
    user_name: str
    guild_id: int
    guild_name: str
    channel_id: int
    channel_name: str

    @classmethod
    def from_message(cls, message: discord.Message) -> "AbuseContext":
        guild = message.guild
        channel = message.channel
        return cls(
            user_id=message.author.id,
            user_name=str(message.author),
            guild_id=guild.id if guild else 0,
            guild_name=guild.name if guild else "?",
            channel_id=channel.id,
            channel_name=getattr(channel, "name", str(channel.id)),
        )


def _clip(text: str, limit: int = 900) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text or "(empty)"
    return text[: limit - 3] + "..."


class AbuseLogger:
    def __init__(self, bot: discord.Client, channel_id: int | None):
        self.bot = bot
        self.channel_id = channel_id

    async def _resolve_channel(self) -> discord.abc.Messageable | None:
        if not self.channel_id:
            return None
        ch = self.bot.get_channel(self.channel_id)
        if ch:
            return ch
        try:
            return await self.bot.fetch_channel(self.channel_id)
        except discord.HTTPException:
            return None

    async def report(
        self,
        event: str,
        ctx: AbuseContext,
        content: str = "",
        note: str = "",
    ):
        if not self.channel_id:
            return

        channel = await self._resolve_channel()
        if not channel:
            return

        title, color = EVENT_META.get(event, (event, discord.Color.greyple()))
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        embed = discord.Embed(title=f"Abuse · {title}", color=color, timestamp=datetime.now(timezone.utc))
        embed.add_field(name="User", value=f"<@{ctx.user_id}>\n`{ctx.user_id}`", inline=True)
        embed.add_field(name="Guild", value=f"{ctx.guild_name}\n`{ctx.guild_id}`", inline=True)
        embed.add_field(name="Channel", value=f"<#{ctx.channel_id}>\n`{ctx.channel_id}`", inline=False)
        embed.add_field(name="Content", value=f"```\n{_clip(content)}\n```", inline=False)
        if note:
            embed.add_field(name="Note", value=_clip(note, 500), inline=False)
        embed.set_footer(text=now)

        try:
            await channel.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())
        except discord.HTTPException as e:
            log.error("Failed to send abuse log: %s", e)
