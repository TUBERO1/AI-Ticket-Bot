import re

import discord

SAFE_MENTIONS = discord.AllowedMentions.none()

_TAG_CLEANUP = [
    (re.compile(r"</?user>", re.I), ""),
    (re.compile(r"\[고객\s*문의\]", re.I), ""),
    (re.compile(r"\[이번\s*질문\s*견적\s*참고\]", re.I), ""),
]

_MENTION_PATTERNS = [
    re.compile(r"@\s*everyone", re.I),
    re.compile(r"@\s*here", re.I),
    re.compile(r"<!everyone>", re.I),
    re.compile(r"<!here>", re.I),
    re.compile(r"<@&\d+>"),
    re.compile(r"@\u200b*everyone", re.I),
    re.compile(r"@\u200b*here", re.I),
    re.compile(r"everyone\s*멘션", re.I),
    re.compile(r"here\s*멘션", re.I),
    re.compile(r"모두\s*멘션", re.I),
    re.compile(r"전체\s*멘션", re.I),
]


def sanitize_reply(text: str) -> str:
    if not text:
        return text

    cleaned = text
    for pattern, repl in _TAG_CLEANUP:
        cleaned = pattern.sub(repl, cleaned)

    for pattern in _MENTION_PATTERNS:
        cleaned = pattern.sub("", cleaned)

    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def compress_lumentia_reply(text: str) -> str:
    if not text:
        return text

    cleaned = sanitize_reply(text)
    if len(cleaned) <= 900 and cleaned.count("\n") <= 12:
        return cleaned

    lines = [ln.strip() for ln in cleaned.splitlines() if ln.strip()]
    if len(lines) <= 10:
        return cleaned[:900].rstrip()

    picked = lines[:8]
    body = "\n".join(picked)
    if len(lines) > 8:
        body += "\n(세부는 lumentia.co.kr 또는 티켓 상담)"
    return body


def compress_rfivem_reply(text: str) -> str:
    if not text:
        return text

    cleaned = sanitize_reply(text)
    if len(cleaned) <= 420 and cleaned.count("\n") <= 6:
        return cleaned

    lines = [ln.strip() for ln in cleaned.splitlines() if ln.strip()]
    picked: list[str] = []
    for line in lines:
        if line.startswith("**판정:**") or line.startswith("**이유:**") or line.startswith("**결과:**") or line.startswith("**참고:**"):
            picked.append(line)
            continue
        if picked and len(picked) < 4 and len("\n".join(picked)) + len(line) < 380:
            picked.append(line)
        if len(picked) >= 4:
            break

    if picked:
        return "\n".join(picked[:4])

    short = cleaned[:380].rstrip()
    if len(cleaned) > 380:
        short += "\n(세부는 운영진 문의)"
    return short


LUMENTIA_URL = "https://www.lumentia.co.kr/"
LUMENTIA_FOOTER = f"-# [외주는 루멘티아]({LUMENTIA_URL})"


def _has_footer(text: str) -> bool:
    return "외주는 루멘티아" in text or "외주는 Lumentia" in text or "lumentia.co.kr" in text


def format_reply_with_footer(text: str) -> str:
    if not text:
        return LUMENTIA_FOOTER
    if _has_footer(text):
        return text
    return f"{text.rstrip()}\n\n{LUMENTIA_FOOTER}"


def split_reply_for_send(text: str) -> tuple[str | None, str | None]:
    if not text:
        return None, LUMENTIA_FOOTER
    if _has_footer(text):
        return text, None
    return text.rstrip(), LUMENTIA_FOOTER
