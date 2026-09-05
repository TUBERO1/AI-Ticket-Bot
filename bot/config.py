import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def _parse_id_list(raw: str) -> list[int]:
    if not raw:
        return []
    return [int(x.strip()) for x in raw.split(",") if x.strip()]


@dataclass(frozen=True)
class AppSettings:
    discord_token: str
    db_path: Path
    developer_ids: list[int] = field(default_factory=list)
    history_limit: int = 20
    debounce_seconds: float = 1.5
    default_ollama_base_url: str = "http://localhost:11434/v1"
    default_ollama_model: str = "exaone3.5:7.8b"
    default_ollama_max_tokens: int = 2048
    default_ollama_temperature: float = 0.7
    abuse_log_channel_id: int | None = None


Settings = AppSettings


def load_settings() -> AppSettings:
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1").strip()
    if not base_url.endswith("/"):
        base_url += "/"

    return AppSettings(
        discord_token=os.getenv("DISCORD_TOKEN", ""),
        db_path=Path(__file__).resolve().parent.parent / "data" / "bot.db",
        developer_ids=_parse_id_list(os.getenv("DEVELOPER_IDS", "")),
        default_ollama_base_url=base_url,
        default_ollama_model=os.getenv("OLLAMA_MODEL", "exaone3.5:7.8b"),
        default_ollama_max_tokens=int(os.getenv("OLLAMA_MAX_TOKENS", "2048")),
        default_ollama_temperature=float(os.getenv("OLLAMA_TEMPERATURE", "0.7")),
        abuse_log_channel_id=int(os.getenv("ABUSE_LOG_CHANNEL_ID", "0") or 0) or None,
    )
