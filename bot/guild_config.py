from dataclasses import dataclass, field


MODE_LUMENTIA = "lumentia"
MODE_RFIVEM = "rfivem"


@dataclass
class GuildConfig:
    guild_id: int
    server_mode: str = MODE_LUMENTIA
    ticket_category_id: int | None = None
    staff_role_id: int | None = None
    support_channel_ids: list[int] = field(default_factory=list)
    custom_prompt: str = ""

    def is_support_channel(self, channel_id: int) -> bool:
        return channel_id in self.support_channel_ids


@dataclass
class LlmRuntimeConfig:
    base_url: str
    model: str
    max_tokens: int
    temperature: float
