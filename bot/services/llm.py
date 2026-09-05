import asyncio
import logging

from openai import OpenAI

from bot.config import AppSettings
from bot.db import Database
from bot.guild_config import MODE_LUMENTIA, MODE_RFIVEM, LlmRuntimeConfig
from bot.services.guard import (
    INJECTION_REPLY,
    RFIVEM_INJECTION_REPLY,
    is_injection_attempt,
    is_unsafe_output,
    prepare_history_for_llm,
)
from bot.services.scope import (
    greeting_reply,
    is_greeting_only,
    is_in_scope,
    is_non_korean_output,
    is_offtopic_output,
    scope_reply,
)
from bot.services.abuse_log import AbuseContext, AbuseLogger
from bot.services.lumentia_quick import try_lumentia_quick_reply
from bot.services.output import compress_lumentia_reply, compress_rfivem_reply, sanitize_reply
from bot.services.prompts import LUMENTIA_SYSTEM_PROMPT, build_pricing_hint
from bot.services.prompts_rfivem import RFIVEM_SYSTEM_PROMPT
from bot.services.rfivem_terms import normalize_rfivem_text, try_rfivem_quick_reply

log = logging.getLogger("bot.llm")

FALLBACK_MESSAGE = (
    "지금은 AI 응답을 생성하지 못했습니다. 잠시 후 다시 시도하거나 "
    "아래 **관리자 호출** 버튼을 눌러 주세요."
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

    def _build_system_prompt(
        self,
        latest_user: str,
        server_mode: str,
        custom_prompt: str = "",
    ) -> str:
        if server_mode == MODE_RFIVEM:
            prompt = RFIVEM_SYSTEM_PROMPT
            extra = custom_prompt.strip()
            if extra:
                prompt += f"\n\n[서버 추가 안내]\n{extra}"
            return prompt

        prompt = LUMENTIA_SYSTEM_PROMPT
        extra = custom_prompt.strip()
        if extra:
            prompt += f"\n\n[서버 전용 안내]\n{extra}"
        pricing_hint = build_pricing_hint(latest_user)
        if pricing_hint:
            prompt += f"\n\n[이번 질문 견적 참고]\n{pricing_hint}"
        return prompt

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
            log.error("Ollama 연결 실패: %s", e)
            return False

    async def _report(self, event: str, ctx: AbuseContext | None, content: str, note: str = ""):
        if self.abuse_log and ctx:
            await self.abuse_log.report(event, ctx, content, note)

    async def chat(
        self,
        history: list[dict],
        custom_prompt: str = "",
        server_mode: str = MODE_LUMENTIA,
        abuse_ctx: AbuseContext | None = None,
    ) -> str:
        truncated = self._truncate_history(history)
        latest = self._latest_user_message(truncated)

        if is_injection_attempt(latest):
            log.warning("인젝션 시도 차단: %s", latest[:80])
            await self._report("injection", abuse_ctx, latest)
            return RFIVEM_INJECTION_REPLY if server_mode == MODE_RFIVEM else INJECTION_REPLY

        if is_greeting_only(latest):
            return greeting_reply(server_mode)

        if not is_in_scope(latest, server_mode):
            log.warning("범위 밖 질문: %s", latest[:80])
            await self._report("out_of_scope", abuse_ctx, latest)
            return scope_reply(server_mode)

        if server_mode == MODE_LUMENTIA:
            quick = try_lumentia_quick_reply(latest, truncated)
            if quick:
                return quick

        if server_mode == MODE_RFIVEM:
            quick = try_rfivem_quick_reply(latest)
            if quick:
                return quick
            latest = normalize_rfivem_text(latest)

        runtime = await self.db.get_llm_runtime(self._defaults())
        client = self._get_client(runtime.base_url)

        rfivem = server_mode == MODE_RFIVEM
        lumentia = server_mode == MODE_LUMENTIA
        max_tokens = min(runtime.max_tokens, 380) if rfivem else min(runtime.max_tokens, 520) if lumentia else runtime.max_tokens
        if rfivem:
            temperature = min(runtime.temperature, 0.25)
        elif lumentia:
            temperature = min(runtime.temperature, 0.35)
        else:
            temperature = min(runtime.temperature, 0.5)

        messages = [{
            "role": "system",
            "content": self._build_system_prompt(latest, server_mode, custom_prompt),
        }]
        messages.extend(prepare_history_for_llm(truncated, server_mode))

        try:
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model=runtime.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            content = response.choices[0].message.content
            if content and content.strip():
                reply = sanitize_reply(content.strip())
                if rfivem:
                    reply = compress_rfivem_reply(reply)
                elif lumentia:
                    reply = compress_lumentia_reply(reply)
                if is_non_korean_output(reply):
                    log.warning("비한국어 응답 차단: %s", reply[:80])
                    await self._report("non_korean_output", abuse_ctx, latest, note=reply[:300])
                    return scope_reply(server_mode)
                if is_offtopic_output(reply, server_mode):
                    log.warning("주제 이탈 응답 차단: %s", reply[:80])
                    await self._report("offtopic_output", abuse_ctx, latest, note=reply[:300])
                    return scope_reply(server_mode)
                if is_unsafe_output(reply, latest):
                    log.warning("위험 응답 차단: %s", reply[:80])
                    await self._report("unsafe_output", abuse_ctx, latest, note=reply[:300])
                    return RFIVEM_INJECTION_REPLY if rfivem else INJECTION_REPLY
                return reply
        except Exception as e:
            log.error("LLM 응답 실패: %s", e)

        return FALLBACK_MESSAGE

    def welcome_message(self, server_mode: str) -> str:
        if server_mode == MODE_RFIVEM:
            return (
                "RFIVEM 법률·RP 판별 AI입니다. (Lumentia 제작 / 법전 v2.0)\n"
                "상황을 짧게 적어 주세요. 판정·이유·결과로 요약해 드립니다.\n"
                "예: 「도주 RP 하다 스토리 RP도 하면?」, 「이미 제압했다고 선언」\n"
                "공식 운영 문의: rfivembusiness@gmail.com"
            )
        return "안녕하세요! 무엇을 도와드릴까요? 문의 내용을 자유롭게 적어 주세요."
