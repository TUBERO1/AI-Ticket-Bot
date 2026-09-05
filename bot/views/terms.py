import discord

from bot.services.terms import TERMS_VERSION, build_terms_embeds

TERMS_VIEW_CUSTOM_ID = "terms:view"
TERMS_AGREE_CUSTOM_ID = "terms:agree"


async def _get_bot_db(interaction: discord.Interaction):
    bot = interaction.client
    db = getattr(bot, "db", None)
    if not db:
        return None, None
    return bot, db


class TermsViewButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="이용약관 확인하기",
            style=discord.ButtonStyle.secondary,
            custom_id=TERMS_VIEW_CUSTOM_ID,
        )

    async def callback(self, interaction: discord.Interaction):
        embeds = build_terms_embeds()
        await interaction.response.send_message(
            embeds=embeds,
            ephemeral=True,
        )


class TermsAgreeButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="동의",
            style=discord.ButtonStyle.success,
            custom_id=TERMS_AGREE_CUSTOM_ID,
        )

    async def callback(self, interaction: discord.Interaction):
        bot, db = await _get_bot_db(interaction)
        if not db:
            await interaction.response.send_message(
                "봇이 준비되지 않았습니다. 잠시 후 다시 시도해 주세요.",
                ephemeral=True,
            )
            return

        await db.set_terms_agreed(interaction.user.id, TERMS_VERSION)

        from bot.utils import process_pending_consult

        pending = await db.get_pending_consult(interaction.user.id)
        if pending:
            await interaction.response.defer(ephemeral=True)
            ok = await process_pending_consult(bot, db, interaction.user.id)
            if ok:
                await interaction.followup.send(
                    "이용약관에 동의하셨습니다. 방금 남기신 문의에 AI가 답변합니다.",
                    ephemeral=True,
                )
            else:
                await interaction.followup.send(
                    "동의가 완료되었습니다. 문의 내용을 다시 보내 주세요.",
                    ephemeral=True,
                )
        else:
            await interaction.response.send_message(
                "이용약관에 동의하셨습니다. 이제 AI 상담을 이용할 수 있습니다.",
                ephemeral=True,
            )


class TermsAgreementView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TermsViewButton())
        self.add_item(TermsAgreeButton())
