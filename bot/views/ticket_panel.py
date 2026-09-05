import discord

TICKET_OPEN_CUSTOM_ID = "ticket:open"
TICKET_STAFF_CUSTOM_ID = "ticket:staff"
TICKET_CLOSE_CUSTOM_ID = "ticket:close"
TICKET_CLOSE_CONFIRM_CUSTOM_ID = "ticket:close_confirm"
TICKET_CLOSE_CANCEL_CUSTOM_ID = "ticket:close_cancel"


async def _get_tickets_cog(interaction: discord.Interaction):
    cog = interaction.client.get_cog("Tickets")
    if not cog:
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "봇이 아직 준비되지 않았습니다. 잠시 후 다시 시도해 주세요.",
                ephemeral=True,
            )
        return None
    return cog


class TicketOpenButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="문의하기",
            style=discord.ButtonStyle.primary,
            custom_id=TICKET_OPEN_CUSTOM_ID,
            emoji="📩",
        )

    async def callback(self, interaction: discord.Interaction):
        cog = await _get_tickets_cog(interaction)
        if cog:
            await cog.open_ticket(interaction)


class TicketStaffButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="관리자 호출",
            style=discord.ButtonStyle.secondary,
            custom_id=TICKET_STAFF_CUSTOM_ID,
            emoji="🔔",
        )

    async def callback(self, interaction: discord.Interaction):
        cog = await _get_tickets_cog(interaction)
        if cog:
            await cog.call_staff(interaction)


class TicketCloseButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="티켓 종료",
            style=discord.ButtonStyle.danger,
            custom_id=TICKET_CLOSE_CUSTOM_ID,
            emoji="🔒",
        )

    async def callback(self, interaction: discord.Interaction):
        cog = await _get_tickets_cog(interaction)
        if cog:
            await cog.request_close(interaction)


class TicketCloseConfirmView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(
        label="종료 확인",
        style=discord.ButtonStyle.danger,
        custom_id=TICKET_CLOSE_CONFIRM_CUSTOM_ID,
    )
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = await _get_tickets_cog(interaction)
        if cog:
            await cog.confirm_close(interaction)

    @discord.ui.button(
        label="취소",
        style=discord.ButtonStyle.secondary,
        custom_id=TICKET_CLOSE_CANCEL_CUSTOM_ID,
    )
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="티켓 종료가 취소되었습니다.", view=None)


class TicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketOpenButton())


class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketStaffButton())
        self.add_item(TicketCloseButton())
