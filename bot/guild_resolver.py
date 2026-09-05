from bot.db import Database
from bot.guild_config import GuildConfig


async def resolve_guild_config(db: Database, guild_id: int) -> GuildConfig:
    stored = await db.get_guild_config(guild_id)
    if stored:
        return stored
    return GuildConfig(guild_id=guild_id)
