import asyncio
import logging

from openai import OpenAI

from bot.config import AppSettings
from bot.db import Database
from bot.guild_config import LlmRuntimeConfig
from bot.services.abuse_log import AbuseContext, AbuseLogger
from bot.services.guard import (
    INJECTION_REPLY,
    is_injection_attempt,
    is_unsafe_output,
    prepare_history_for_llm,
)
from bot.services.output import sanitize_reply
from bot.services.prompts import build_system_prompt
from bot.services.scope import greeting_reply, is_greeting_only

log = logging.getLogger("bot.llm")

FALLBACK_MESSAGE = (
    "I couldn't generate a reply right now. Try again in a moment, "
    "or press **Call Staff**."
)


class LlmService:
    def __init__(self, settings: AppSettings, db: Database, abuse_log: AbuseLogger | None = None):
        self.settings = settings
        self.db = db
        self.abuse_log = abuse_log
        self._client: OpenAI | None = None
        self._client_url: str | None = None

    def _defaults(self) -> LlmRuntimeConfig:
        return LlmRuntimeConfig(
            base_url=self.settings.default_ollama_base_url,
            model=self.settings.default_ollama_model,
            max_tokens=self.settings.default_ollama_max_tokens,
            temperature=self.settings.default_ollama_temperature,
        )

    def _get_client(self, base_url: str) -> OpenAI:
        if self._client is None or self._client_url != base_url:
            self._client = OpenAI(api_key="ollama", base_url=base_url)
            self._client_url = base_url
        return self._client

    def _truncate_history(self, history: list[dict]) -> list[dict]:
        limit = self.settings.history_limit
        if len(history) <= limit:
            return history
        return history[-limit:]

    def _latest_user_message(self, history: list[dict]) -> str:
        for item in reversed(history):
            if item.get("role") == "user":
                return item.get("content", "")
        return ""

    async def health_check(self) -> bool:
        try:
            runtime = await self.db.get_llm_runtime(self._defaults())
            await asyncio.to_thread(self._get_client(runtime.base_url).models.list)
            return True
        except Exception as e:
            log.error("Ollama connection failed: %s", e)
            return False

    async def _report(self, event: str, ctx: AbuseContext | None, content: str, note: str = ""):
        if self.abuse_log and ctx:
            await self.abuse_log.report(event, ctx, content, note)

    async def chat(
        self,
        history: list[dict],
        custom_prompt: str = "",
        abuse_ctx: AbuseContext | None = None,
    ) -> str:
        truncated = self._truncate_history(history)
        latest = self._latest_user_message(truncated)

        if is_injection_attempt(latest):
            log.warning("Blocked injection attempt: %s", latest[:80])
            await self._report("injection", abuse_ctx, latest)
            return INJECTION_REPLY

        if is_greeting_only(latest):
            return greeting_reply()

        runtime = await self.db.get_llm_runtime(self._defaults())
        client = self._get_client(runtime.base_url)

        messages = [{
            "role": "system",
            "content": build_system_prompt(custom_prompt),
        }]
        messages.extend(prepare_history_for_llm(truncated))

        try:
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model=runtime.model,
                messages=messages,
                temperature=min(runtime.temperature, 0.5),
                max_tokens=min(runtime.max_tokens, 600),
            )
            content = response.choices[0].message.content
            if content and content.strip():
                reply = sanitize_reply(content.strip())
                if is_unsafe_output(reply, latest):
                    log.warning("Blocked unsafe output: %s", reply[:80])
                    await self._report("unsafe_output", abuse_ctx, latest, note=reply[:300])
                    return INJECTION_REPLY
                return reply
        except Exception as e:
            log.error("LLM reply failed: %s", e)

        return FALLBACK_MESSAGE

    def welcome_message(self) -> str:
        return "Hi. Send your question and I will reply."
