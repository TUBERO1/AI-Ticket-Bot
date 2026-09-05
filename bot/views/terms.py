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
            label="View Terms",
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
            label="Agree",
            style=discord.ButtonStyle.success,
            custom_id=TERMS_AGREE_CUSTOM_ID,
        )

    async def callback(self, interaction: discord.Interaction):
        bot, db = await _get_bot_db(interaction)
        if not db:
            await interaction.response.send_message(
                "The bot is not ready yet. Try again in a moment.",
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
                    "Thanks. The AI will answer the question you just sent.",
                    ephemeral=True,
                )
            else:
                await interaction.followup.send(
                    "Agreed. Please send your question again.",
                    ephemeral=True,
                )
        else:
            await interaction.response.send_message(
                "Agreed. You can use AI support now.",
                ephemeral=True,
            )


class TermsAgreementView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TermsViewButton())
        self.add_item(TermsAgreeButton())
