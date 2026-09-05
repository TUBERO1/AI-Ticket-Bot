import logging
from dataclasses import dataclass
from datetime import datetime, timezone

import discord

log = logging.getLogger("bot.abuse")

EVENT_META = {
    "injection": ("프롬프트 인젝션", discord.Color.red()),
    "out_of_scope": ("범위 밖 문의", discord.Color.orange()),
    "non_korean_output": ("비한국어 응답 차단", discord.Color.gold()),
    "offtopic_output": ("주제 이탈 응답", discord.Color.gold()),
    "unsafe_output": ("위험 응답 차단", discord.Color.red()),
    "spam_repeat": ("반복 스팸", discord.Color.dark_red()),
}


@dataclass
class AbuseContext:
    user_id: int
    user_name: str
    guild_id: int
    guild_name: str
    channel_id: int
    channel_name: str
    server_mode: str = "lumentia"

    @classmethod
    def from_message(cls, message: discord.Message, server_mode: str = "lumentia") -> "AbuseContext":
        guild = message.guild
        channel = message.channel
        return cls(
            user_id=message.author.id,
            user_name=str(message.author),
            guild_id=guild.id if guild else 0,
            guild_name=guild.name if guild else "?",
            channel_id=channel.id,
            channel_name=getattr(channel, "name", str(channel.id)),
            server_mode=server_mode,
        )


def _clip(text: str, limit: int = 900) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text or "(내용 없음)"
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
        except discord.HTTPException as e:
            log.error("악용 로그 채널 조회 실패: %s", e)
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

        embed = discord.Embed(title=f"악용 탐지 · {title}", color=color, timestamp=datetime.now(timezone.utc))
        embed.add_field(name="유저", value=f"<@{ctx.user_id}>\n`{ctx.user_id}`", inline=True)
        embed.add_field(name="서버", value=f"{ctx.guild_name}\n`{ctx.guild_id}`", inline=True)
        embed.add_field(name="모드", value=ctx.server_mode, inline=True)
        embed.add_field(name="채널", value=f"<#{ctx.channel_id}>\n`{ctx.channel_id}`", inline=False)
        embed.add_field(name="내용", value=f"```\n{_clip(content)}\n```", inline=False)
        if note:
            embed.add_field(name="비고", value=_clip(note, 500), inline=False)
        embed.set_footer(text=now)

        try:
            await channel.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())
        except discord.HTTPException as e:
            log.error("악용 로그 전송 실패: %s", e)
