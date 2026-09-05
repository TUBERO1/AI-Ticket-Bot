import discord

from bot.config import AppSettings


def is_developer(user_id: int, settings: AppSettings) -> bool:
    return user_id in settings.developer_ids


async def deny_unless_developer(interaction: discord.Interaction, settings: AppSettings) -> bool:
    if is_developer(interaction.user.id, settings):
        return True
    msg = "이 명령은 **봇 개발자**만 사용할 수 있습니다."
    if interaction.response.is_done():
        await interaction.followup.send(msg, ephemeral=True)
    else:
        await interaction.response.send_message(msg, ephemeral=True)
    return False
